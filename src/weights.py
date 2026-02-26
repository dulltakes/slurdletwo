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
        print(f"\nLoading {short_name} via Apple Metal...")
        model = SentenceTransformer(model_id, device='mps')

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

        results[short_name] = df_weights

    print("\nAll done! Files saved:")
    for short_name in MODELS:
        print(f"  - target_weights_{short_name}.csv")

    return results


if __name__ == "__main__":
    generate_similarity_weights()
