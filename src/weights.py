import sqlite3

import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import DATA_DIR, SLURS_DB

MODELS = {
    "paraphrase-multilingual-mpnet-base-v2": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
}


def generate_similarity_weights():
    conn = sqlite3.connect(SLURS_DB)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT target FROM slurs ORDER BY target ASC;")
    targets = [row[0] for row in cursor.fetchall()]
    conn.close()

    results = {}

    for short_name, model_id in MODELS.items():
        print(f"\nLoading {short_name}...")
        model = SentenceTransformer(model_id)

        texts_to_encode = targets

        print(f"  Generating embeddings for {len(targets)} targets...")
        embeddings = model.encode(texts_to_encode, show_progress_bar=True)

        print("  Calculating cosine similarity...")
        similarity_matrix = cosine_similarity(embeddings)

        df_weights = pd.DataFrame(similarity_matrix, index=targets, columns=targets)

        output_path = DATA_DIR / f"target_weights_{short_name}.csv"
        df_weights.to_csv(output_path)
        print(f"  Saved to {output_path}")

        print(f"\n  Top 25 closest target pairs for {short_name} (excluding self-similarity):")
        pairs: list[tuple[float, str, str]] = []
        for i in range(len(targets)):
            for j in range(i + 1, len(targets)):
                val = df_weights.iloc[i, j]
                pairs.append((float(val), targets[i], targets[j]))  # type: ignore
        
        pairs.sort(reverse=True, key=lambda x: x[0])
        for val, t1, t2 in pairs[:25]:
            print(f"    {t1} <-> {t2}: {val:.4f}")

        results[short_name] = df_weights

    print("\nAll done! Files saved:")
    for short_name in MODELS:
        print(f"  - target_weights_{short_name}.csv")

    return results



def qa_weights(custom_path=None):
    from pathlib import Path

    import pandas as pd

    from src.config import DATA_DIR
    
    weights_path = Path(custom_path) if custom_path else DATA_DIR / "target_weights_paraphrase-multilingual-mpnet-base-v2.csv"
    if not weights_path.exists():
        print(f"Error: {weights_path} not found. Run --weights-combined first or provide a valid path.")
        return
        
    df_weights = pd.read_csv(weights_path, index_col=0)
    targets = df_weights.index.tolist()
    
    pairs: list[tuple[float, str, str]] = []
    for i in range(len(targets)):
        for j in range(i + 1, len(targets)):
            val = df_weights.iloc[i, j]
            pairs.append((float(val), targets[i], targets[j]))  # type: ignore
            
    pairs.sort(reverse=True, key=lambda x: x[0])
    
    print(f"\n--- TOP 25 MATCHES FOR {weights_path.name} ---")
    for val, t1, t2 in pairs[:25]:
        print(f"  {t1} <-> {t2}: {val:.4f}")
        
    mid_idx = len(pairs) // 2
    print("\n--- MIDDLE 10 MATCHES ---")
    for val, t1, t2 in pairs[mid_idx - 5: mid_idx + 5]:
        print(f"  {t1} <-> {t2}: {val:.4f}")
        
    print("\n--- BOTTOM 10 MATCHES ---")
    for val, t1, t2 in pairs[-10:]:
        print(f"  {t1} <-> {t2}: {val:.4f}")


if __name__ == "__main__":
    generate_similarity_weights()
