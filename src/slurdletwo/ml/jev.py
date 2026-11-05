import argparse
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, cast

import pandas as pd
from typesafe_sdk import Noul, TypeSafeClient

from slurdletwo.config import (
    DATA_DIR,
    MAX_SEMANTIC_SIMILARITY,
    MIN_SEMANTIC_SIMILARITY,
    SLURS_DB,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

DEFAULT_JEV_WEIGHTS_FILE = DATA_DIR / "target_weights_typesafe-jev.csv"
DEFAULT_CHECKPOINT_FILE = DATA_DIR / "jev_weights_checkpoint.json"
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api"
DEFAULT_JEV_MODEL = "typesafe/jev-1.14"


def fetch_unique_demographic_targets() -> list[str]:
    """Retrieve all distinct demographic targets from the SQLite database in alphabetical order."""
    if not SLURS_DB.exists():
        raise FileNotFoundError(
            f"Database file not found at {SLURS_DB}. Run database initialization first."
        )

    conn = sqlite3.connect(SLURS_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT target FROM slurs ORDER BY target ASC;")
    targets = [row[0] for row in cursor.fetchall()]
    conn.close()
    return targets


def _load_pairwise_checkpoint(checkpoint_path: Path) -> dict[str, float]:
    """Load previously calculated pairwise similarities from disk."""
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, OSError) as err:
            logger.warning(
                "Could not read checkpoint file %s: %s. Starting fresh.",
                checkpoint_path,
                err,
            )
    return {}


def _save_pairwise_checkpoint(checkpoint_path: Path, data: dict[str, float]) -> None:
    """Save calculated pairwise similarities to disk atomically."""
    temp_path = checkpoint_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    temp_path.replace(checkpoint_path)


def _make_pair_key(target_a: str, target_b: str) -> str:
    """Produce a deterministic, symmetric key for two demographic target labels."""
    return (
        f"{target_a}|||{target_b}"
        if target_a < target_b
        else f"{target_b}|||{target_a}"
    )


def generate_jev_weights(
    batch_size: int = 35,
    sample_limit: int | None = None,
    checkpoint_path: Path | None = None,
    output_path: Path | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> pd.DataFrame:
    """Generate pairwise demographic similarity weights using TypeSafe AI's Jev model via OpenRouter.

    Args:
        batch_size: Number of parallel Noul questions to bundle per API request.
        sample_limit: Optional limit on the number of targets to evaluate (for testing).
        checkpoint_path: File path to store and resume incremental progress.
        output_path: File path where the resulting symmetric matrix CSV is written.
        api_key: OpenRouter or TypeSafe API key (falls back to OPENROUTER_API_KEY / TYPESAFE_API_KEY).
        base_url: API root endpoint (defaults to https://openrouter.ai/api).
        model: Model identifier on OpenRouter (defaults to typesafe/jev-1.14).

    Returns:
        A symmetric pandas DataFrame with pairwise probabilities between targets.
    """
    resolved_api_key = (
        api_key
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("TYPESAFE_API_KEY")
    )
    if not resolved_api_key:
        raise ValueError(
            "API key missing. Set the OPENROUTER_API_KEY or TYPESAFE_API_KEY environment variable, "
            "or pass api_key explicitly."
        )

    resolved_base_url = base_url or os.environ.get(
        "OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE_URL
    )
    resolved_model = model or DEFAULT_JEV_MODEL
    resolved_checkpoint = checkpoint_path or DEFAULT_CHECKPOINT_FILE
    resolved_output = output_path or DEFAULT_JEV_WEIGHTS_FILE

    all_targets = fetch_unique_demographic_targets()
    if sample_limit is not None and sample_limit > 0:
        targets = all_targets[:sample_limit]
        logger.info(
            "Evaluating a sample of %d targets (out of %d total)",
            len(targets),
            len(all_targets),
        )
    else:
        targets = all_targets
        logger.info("Evaluating all %d unique demographic targets", len(targets))

    # Calculate total unique pairs (unordered, excluding self-pairs)
    target_pairs: list[tuple[str, str]] = []
    for i in range(len(targets)):
        for j in range(i + 1, len(targets)):
            target_pairs.append((targets[i], targets[j]))

    total_pairs_count = len(target_pairs)
    logger.info("Total unique pairs to evaluate: %d", total_pairs_count)

    pair_scores: dict[str, float] = _load_pairwise_checkpoint(resolved_checkpoint)
    existing_count = sum(
        1 for a, b in target_pairs if _make_pair_key(a, b) in pair_scores
    )
    logger.info("Found %d previously evaluated pairs in checkpoint", existing_count)

    # Group uncomputed pairs by source target for efficient question bundling
    pending_targets_map: dict[str, list[str]] = {}
    for a, b in target_pairs:
        pair_key = _make_pair_key(a, b)
        if pair_key not in pair_scores:
            pending_targets_map.setdefault(a, []).append(b)

    remaining_pairs_count = total_pairs_count - existing_count
    logger.info("Pairs remaining to evaluate: %d", remaining_pairs_count)

    if remaining_pairs_count > 0:
        with TypeSafeClient(
            api_key=resolved_api_key, base_url=resolved_base_url
        ) as client:
            completed_in_session = 0
            for source_target, candidates in pending_targets_map.items():
                for idx in range(0, len(candidates), batch_size):
                    chunk = candidates[idx : idx + batch_size]
                    state: dict[str, Any] = {"source_demographic": source_target}

                    question_map: dict[str, str] = {}
                    questions: dict[str, Noul] = {}
                    for q_idx, candidate in enumerate(chunk):
                        q_id = f"rel_{q_idx}"
                        question_map[q_id] = candidate
                        questions[q_id] = Noul(
                            instructions=(
                                f"Is the demographic group '{candidate}' culturally, geographically, "
                                f"linguistically, or ethnically related to `source_demographic`?"
                            )
                        )

                    try:
                        response = client.system_one(
                            state=state,
                            questions=questions,
                            model=resolved_model,
                        )

                        for q_id, candidate in question_map.items():
                            if q_id in response.nouls:
                                probability = float(response.nouls[q_id].noul)
                            elif q_id in response.answers:
                                answer = response.answers[q_id]
                                probability = float(getattr(answer, "noul", 0.0))
                            else:
                                probability = 0.0

                            pair_key = _make_pair_key(source_target, candidate)
                            pair_scores[pair_key] = round(probability, 4)

                        completed_in_session += len(chunk)
                        total_done = existing_count + completed_in_session
                        logger.info(
                            "Progress: %d / %d pairs (%.1f%%) [Batch with source '%s' (%d items)]",
                            total_done,
                            total_pairs_count,
                            (total_done / total_pairs_count) * 100.0,
                            source_target,
                            len(chunk),
                        )

                        # Checkpoint incrementally to protect against interruptions
                        _save_pairwise_checkpoint(resolved_checkpoint, pair_scores)

                    except Exception as err:
                        logger.error(
                            "API error evaluating chunk for source '%s' (items: %s): %s",
                            source_target,
                            chunk,
                            err,
                        )
                        _save_pairwise_checkpoint(resolved_checkpoint, pair_scores)
                        raise

    # Construct the full symmetric N x N similarity matrix
    matrix_size = len(targets)
    matrix = [
        [1.0 if r == c else 0.0 for c in range(matrix_size)] for r in range(matrix_size)
    ]

    for r in range(matrix_size):
        for c in range(r + 1, matrix_size):
            t_r, t_c = targets[r], targets[c]
            pair_key = _make_pair_key(t_r, t_c)
            sim_score = pair_scores.get(pair_key, 0.0)
            matrix[r][c] = sim_score
            matrix[c][r] = sim_score

    weights_df = pd.DataFrame(matrix, index=targets, columns=targets)
    weights_df.to_csv(resolved_output)
    logger.info(
        "Successfully generated symmetric weights matrix (%d x %d): %s",
        matrix_size,
        matrix_size,
        resolved_output,
    )
    return weights_df


def qa_weights(custom_path: str | Path | None = None) -> None:
    """Inspect and validate the quality of a generated weights matrix CSV file."""
    weights_path = Path(custom_path) if custom_path else DEFAULT_JEV_WEIGHTS_FILE
    if not weights_path.exists():
        print(
            f"Error: Weights file '{weights_path}' not found. Run weight generation first or provide a valid path."
        )
        return

    df_weights = pd.read_csv(weights_path, index_col=0)
    targets = df_weights.index.tolist()
    total_targets = len(targets)

    pairs: list[tuple[float, str, str]] = []
    for i in range(total_targets):
        for j in range(i + 1, total_targets):
            val = float(cast(Any, df_weights.iloc[i, j]))
            pairs.append((val, str(targets[i]), str(targets[j])))

    pairs.sort(reverse=True, key=lambda x: x[0])
    total_pairs = len(pairs)

    print("=" * 64)
    print(f"QA ANALYSIS: {weights_path.name}")
    print(f"Total Targets: {total_targets} | Evaluated Pairs: {total_pairs}")
    print(
        f"Semantic Corridor: {MIN_SEMANTIC_SIMILARITY:.2f} <= s <= {MAX_SEMANTIC_SIMILARITY:.2f}"
    )
    print("=" * 64)

    print("\n--- TOP 25 CLOSEST DEMOGRAPHIC PAIRS (EXCLUDING SELF-MATCHES) ---")
    for val, t1, t2 in pairs[:25]:
        print(f"  {t1:<28} <-> {t2:<28} : {val:.4f}")

    mid_idx = total_pairs // 2
    print("\n--- MIDDLE 10 DEMOGRAPHIC PAIRS ---")
    for val, t1, t2 in pairs[mid_idx - 5 : mid_idx + 5]:
        print(f"  {t1:<28} <-> {t2:<28} : {val:.4f}")

    print("\n--- BOTTOM 10 DEMOGRAPHIC PAIRS ---")
    for val, t1, t2 in pairs[-10:]:
        print(f"  {t1:<28} <-> {t2:<28} : {val:.4f}")

    # Corridor statistics
    below_corridor = sum(1 for val, _, _ in pairs if val < MIN_SEMANTIC_SIMILARITY)
    in_corridor = sum(
        1
        for val, _, _ in pairs
        if MIN_SEMANTIC_SIMILARITY <= val <= MAX_SEMANTIC_SIMILARITY
    )
    above_corridor = sum(1 for val, _, _ in pairs if val > MAX_SEMANTIC_SIMILARITY)

    print("\n--- CORRIDOR DISTRIBUTION ---")
    print(
        f"  Below Corridor (< {MIN_SEMANTIC_SIMILARITY:.2f})       : {below_corridor:5d} pairs ({below_corridor / total_pairs * 100.0:5.1f}%) [Obvious Non-Matches]"
    )
    print(
        f"  Inside Corridor ({MIN_SEMANTIC_SIMILARITY:.2f} - {MAX_SEMANTIC_SIMILARITY:.2f}) : {in_corridor:5d} pairs ({in_corridor / total_pairs * 100.0:5.1f}%) [Viable Distractors]"
    )
    print(
        f"  Above Corridor (> {MAX_SEMANTIC_SIMILARITY:.2f})       : {above_corridor:5d} pairs ({above_corridor / total_pairs * 100.0:5.1f}%) [Near-Synonyms]"
    )
    print("=" * 64)


def main():
    parser = argparse.ArgumentParser(
        description="Generate and evaluate pairwise demographic similarities using TypeSafe Jev via OpenRouter"
    )
    parser.add_argument(
        "--generate", action="store_true", help="Generate similarity matrix for targets"
    )
    parser.add_argument(
        "--qa-weights",
        nargs="?",
        const="",
        help="Run QA evaluation on a generated weights matrix (optional path)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Limit generation to first N targets for testing",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=35,
        help="Number of questions bundled per API request (default: 35)",
    )
    parser.add_argument(
        "--clear-checkpoint",
        action="store_true",
        help="Delete checkpoint and start generation fresh",
    )

    args = parser.parse_args()

    if args.clear_checkpoint and DEFAULT_CHECKPOINT_FILE.exists():
        DEFAULT_CHECKPOINT_FILE.unlink()
        print(f"Cleared checkpoint file: {DEFAULT_CHECKPOINT_FILE}")

    if args.qa_weights is not None:
        path = None if args.qa_weights == "" else args.qa_weights
        qa_weights(path)
        return

    if args.generate:
        generate_jev_weights(batch_size=args.batch_size, sample_limit=args.sample)
        qa_weights()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
