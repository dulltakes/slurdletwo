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

def qa_weights_llm(custom_path=None):
    import json
    import random
    from pathlib import Path

    import pandas as pd
    from google import genai

    from src.config import DATA_DIR
    
    weights_path = Path(custom_path) if custom_path else DATA_DIR / "target_weights_paraphrase-multilingual-mpnet-base-v2.csv"
    if not weights_path.exists():
        print(f"Error: {weights_path} not found.")
        return
        
    df_weights = pd.read_csv(weights_path, index_col=0)
    targets = df_weights.index.tolist()
    
    valid_pairs = []
    for i in range(len(targets)):
        for j in range(i + 1, len(targets)):
            val = df_weights.iloc[i, j]
            if 0.3 < float(val) < 0.8:  # type: ignore
                valid_pairs.append((targets[i], targets[j], val))
                
    if len(valid_pairs) > 100:
        sampled_pairs = random.sample(valid_pairs, 100)
    else:
        sampled_pairs = valid_pairs
        
    if not sampled_pairs:
        print("No pairs found within the 0.3 - 0.8 range.")
        return
        
    print(f"Evaluating {len(sampled_pairs)} pairs with Gemini LLM-as-a-Judge...")
    client = genai.Client()
    
    prompt_pairs = [f"{t1} <-> {t2}" for t1, t2, _ in sampled_pairs]
    prompt = f"""You are an expert trivia designer. Given the following pairs of demographic groups, evaluate if they are plausible distractors for each other (i.e. related enough to be tricky, but distinct enough to not be ambiguous). 
Output a JSON object where the keys are the exact pair strings provided, and the values are boolean true/false.

PAIRS:
{json.dumps(prompt_pairs)}
"""
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    )
    
    if not response.text:
        print("Error: Gemini returned an empty response.")
        return
        
    results = json.loads(response.text)
    valid_count = sum(1 for v in results.values() if v is True)
    total = len(results)
    
    print("\nLLM QA Results:")
    print(f"  Valid Distractors: {valid_count} / {total} ({(valid_count/total)*100:.1f}%)")
    
    invalid_pairs = [k for k, v in results.items() if v is False]
    if invalid_pairs:
        print("\nExamples flagged as INVALID by Gemini:")
        for ip in invalid_pairs[:10]:
            print(f"  - {ip}")

def qa_weights_reranker(custom_path=None):
    import random
    from pathlib import Path

    import numpy as np
    import pandas as pd
    from sentence_transformers.cross_encoder import CrossEncoder

    from src.config import DATA_DIR
    
    weights_path = Path(custom_path) if custom_path else DATA_DIR / "target_weights_paraphrase-multilingual-mpnet-base-v2.csv"
    if not weights_path.exists():
        print(f"Error: {weights_path} not found.")
        return
        
    df_weights = pd.read_csv(weights_path, index_col=0)
    targets = df_weights.index.tolist()
    
    pairs = []
    scores = []
    for i in range(len(targets)):
        for j in range(i + 1, len(targets)):
            pairs.append((targets[i], targets[j]))
            scores.append(df_weights.iloc[i, j])
            
    if len(pairs) > 500:
        indices = random.sample(range(len(pairs)), 500)
        sampled_pairs = [pairs[i] for i in indices]
        sampled_scores = [scores[i] for i in indices]
    else:
        sampled_pairs = pairs
        sampled_scores = scores
        
    print(f"Loading CrossEncoder (cross-encoder/stsb-roberta-large) for {len(sampled_pairs)} pairs...")
    model = CrossEncoder('cross-encoder/stsb-roberta-large')
    
    print("Scoring with CrossEncoder...")
    cross_scores = model.predict(sampled_pairs, show_progress_bar=True)
    
    correlation = np.corrcoef(np.array(sampled_scores, dtype=float), cross_scores)[0, 1]
    
    print("\nCrossEncoder QA Results:")
    print(f"  Pearson Correlation with original weights: {correlation:.4f}")
    if correlation > 0.8:
        print("  Status: EXCELLENT (Highly robust matrix)")
    elif correlation > 0.6:
        print("  Status: GOOD (Acceptable matrix)")
    else:
        print("  Status: POOR (Matrix does not align with deep semantic similarity)")
    


if __name__ == "__main__":
    generate_similarity_weights()
