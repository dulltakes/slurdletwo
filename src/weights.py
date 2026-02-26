import sqlite3

import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import DATA_DIR, SLURS_DB


def generate_similarity_weights():
    conn = sqlite3.connect(SLURS_DB)
    cursor = conn.cursor()

    # 1. Have SQLite sort the unique targets alphabetically right out of the gate
    cursor.execute("SELECT DISTINCT target FROM slurs ORDER BY target ASC;")
    targets = [row[0] for row in cursor.fetchall()]
    conn.close()

    print("Loading BGE model via Apple Metal...")
    # 2. Load your high-accuracy model using Mac hardware acceleration
    model = SentenceTransformer('BAAI/bge-large-en-v1.5', device='mps')

    print("Generating embeddings...")
    embeddings = model.encode(targets)

    print("Calculating cosine similarity weights...")
    similarity_matrix = cosine_similarity(embeddings)

    # 3. Because 'targets' was sorted in step 1, the DataFrame is perfectly alphabetical!
    df_weights = pd.DataFrame(similarity_matrix, index=targets, columns=targets)

    df_weights.to_csv(DATA_DIR / "target_weights.csv")
    print(f"Weights saved to {DATA_DIR / 'target_weights.csv'}!")

    return df_weights


if __name__ == "__main__":
    generate_similarity_weights()
