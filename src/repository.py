from src.models import db, Slur
from sqlalchemy.sql.expression import func
from sqlalchemy import text
import re

def get_random_slur_record():
    return Slur.query.order_by(func.random()).first()

def get_all_unique_targets():
    results = Slur.query.with_entities(Slur.target).distinct().all()
    return [r[0] for r in results]

def get_targets_excluding_substrings(target, limit=4):
    cleaned_target = re.sub(r"s\b", "", target, flags=re.IGNORECASE)
    words = re.split(r"[\s/]+", cleaned_target)
    
    conditions = []
    params = {}
    for i, word in enumerate(words):
        if len(word) > 2:
            conditions.append(f"(target NOT LIKE :word_like_{i} AND :word_exact_{i} NOT LIKE '%' || target || '%')")
            params[f"word_like_{i}"] = f"%{word}%"
            params[f"word_exact_{i}"] = word
            
    if not conditions:
        conditions.append("(target NOT LIKE :clean_like AND :clean_exact NOT LIKE '%' || target || '%')")
        params["clean_like"] = f"%{cleaned_target}%"
        params["clean_exact"] = cleaned_target
        
    where_clause = " AND ".join(conditions)
    sql = text(f"""
        SELECT DISTINCT target 
        FROM slurs 
        WHERE {where_clause} 
        ORDER BY RANDOM() 
        LIMIT :limit
    """)
    params["limit"] = limit
    
    results = db.session.execute(sql, params).fetchall()
    return [r[0] for r in results]
