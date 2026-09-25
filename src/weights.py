import sqlite3

import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import DATA_DIR, SLURS_DB

MODELS = {
    "paraphrase-multilingual-mpnet-base-v2": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "bge-large-en-v1.5": "BAAI/bge-large-en-v1.5",
}

# BGE models perform better with this task-specific prefix
BGE_PREFIX = "Represent the ethnic/demographic group: "


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

        # Apply prefix only for BGE models
        if "bge" in short_name:
            texts_to_encode = [BGE_PREFIX + t for t in targets]
            print(f"  Encoding with prefix: '{BGE_PREFIX}'")
        else:
            texts_to_encode = targets

        print(f"  Generating embeddings for {len(targets)} targets...")
        embeddings = model.encode(texts_to_encode, show_progress_bar=True)

        print(f"  Calculating cosine similarity...")
        similarity_matrix = cosine_similarity(embeddings)

        df_weights = pd.DataFrame(similarity_matrix, index=targets, columns=targets)

        output_path = DATA_DIR / f"target_weights_{short_name}.csv"
        df_weights.to_csv(output_path)
        print(f"  Saved to {output_path}")

        print(f"\n  Top 25 closest target pairs for {short_name} (excluding self-similarity):")
        pairs = []
        for i in range(len(targets)):
            for j in range(i + 1, len(targets)):
                val = df_weights.iloc[i, j]
                pairs.append((val, targets[i], targets[j]))
        
        pairs.sort(reverse=True, key=lambda x: x[0])
        for val, t1, t2 in pairs[:25]:
            print(f"    {t1} <-> {t2}: {val:.4f}")

        results[short_name] = df_weights

    print("\nAll done! Files saved:")
    for short_name in MODELS:
        print(f"  - target_weights_{short_name}.csv")

    return results


def generate_gemini_weights():
    import os
    import json
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        return

    print("\nGenerating weights via Gemini 3.1 Pro...")
    conn = sqlite3.connect(SLURS_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT target FROM slurs ORDER BY target ASC;")
    targets = [row[0] for row in cursor.fetchall()]
    conn.close()

    client = genai.Client()
    
    prompt = f"""You are an expert sociologist and game designer for a trivia application. 
Below is a list of ethnic, national, and demographic groups. 
For each group in the list, identify 5 to 10 other groups from the exact same list that are the most semantically related (e.g., sharing geographic proximity, cultural history, or commonly grouped together). 
These will be used as plausible incorrect distractors in a multiple-choice question.

Your output must be valid JSON where keys are the target groups and values are lists of related groups.
Only output groups that are in the provided list.

TARGETS:
{json.dumps(targets)}
"""

    print("Calling Gemini API...")
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
    )
    
    related_map = json.loads(response.text)
    
    missing_targets = [t for t in targets if t not in related_map]
    if missing_targets:
        print(f"\nWarning: Gemini failed to process {len(missing_targets)} targets:")
        for mt in missing_targets:
            print(f"  - {mt}")
    else:
        print("\nSuccess: Gemini provided mappings for all targets.")
        
    df_weights = pd.DataFrame(0.0, index=targets, columns=targets)
    
    for target, related in related_map.items():
        if target in df_weights.index:
            df_weights.at[target, target] = 1.0 # self similarity
            for r in related:
                if r in df_weights.columns:
                    df_weights.at[target, r] = 0.5
                    
    output_path = DATA_DIR / "target_weights_gemini-2.5-pro.csv"
    df_weights.to_csv(output_path)
    print(f"Saved to {output_path}")

    print("\nTop 25 closest target pairs (excluding self-similarity):")
    pairs = []
    for target in df_weights.index:
        for col in df_weights.columns:
            if target != col:
                val = df_weights.at[target, col]
                if val > 0.0:
                    pairs.append((val, target, col))
                    
    # Sort by weight descending (though mostly they will be 0.5)
    pairs.sort(reverse=True, key=lambda x: x[0])
    
    for val, t1, t2 in pairs[:25]:
        print(f"  {t1} <-> {t2}: {val}")


if __name__ == "__main__":
    generate_similarity_weights()
