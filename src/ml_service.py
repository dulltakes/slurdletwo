import pandas as pd
import random
from src.config import DATA_DIR, MIN_SEMANTIC_SIMILARITY, MAX_SEMANTIC_SIMILARITY

class TargetSimilarityService:
    def __init__(self):
        self.weights_df = pd.DataFrame()
        
    def load(self):
        weights_path_mpnet = DATA_DIR / "target_weights_paraphrase-multilingual-mpnet-base-v2.csv"
        weights_path_combined = DATA_DIR / "target_weights_combined.csv"
        weights_path_legacy = DATA_DIR / "target_weights_bge-large-en-v1.5.csv"
        
        if weights_path_mpnet.exists():
            self.weights_df = pd.read_csv(weights_path_mpnet, index_col=0)
        elif weights_path_combined.exists():
            self.weights_df = pd.read_csv(weights_path_combined, index_col=0)
        elif weights_path_legacy.exists():
            self.weights_df = pd.read_csv(weights_path_legacy, index_col=0)
            
    def get_similar_targets(self, target, count=4):
        if self.weights_df.empty or target not in self.weights_df.index:
            return None
            
        similarities = self.weights_df.loc[target]
        valid_targets = similarities[
            (similarities > MIN_SEMANTIC_SIMILARITY) & 
            (similarities < MAX_SEMANTIC_SIMILARITY)
        ].index.tolist()
        
        if len(valid_targets) >= count:
            return random.sample(valid_targets, count)
        return None

ml_service = TargetSimilarityService()
