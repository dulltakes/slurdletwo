import random
import sqlite3
import re
import pandas as pd

from src.config import DATA_DIR, SLURS_DB

WEIGHTS_DF = None

def get_weights_df():
    global WEIGHTS_DF
    if WEIGHTS_DF is None:
        weights_path = DATA_DIR / "target_weights_bge-large-en-v1.5.csv"
        if weights_path.exists():
            WEIGHTS_DF = pd.read_csv(weights_path, index_col=0)
        else:
            WEIGHTS_DF = pd.DataFrame()
    return WEIGHTS_DF

def connect(command, params=(), multiple_lines=False):
    try:
        conn = sqlite3.connect(SLURS_DB)
        cursor = conn.cursor()
        cursor.execute(command, params)
        return (
            [i[0] for i in cursor.fetchall()] if multiple_lines else cursor.fetchone()
        )
    except sqlite3.Error as e:
        print(e)
    finally:
        conn.close()

def get_targets():
    command = """SELECT DISTINCT target from slurs;"""
    return connect(command, multiple_lines=True)

def generate_slur():
    command = """SELECT * from slurs ORDER BY RANDOM() LIMIT 1;"""
    return connect(command, multiple_lines=False)

def generate_other_targets(slur):
    target = slur[1]
    
    # Try semantic selection first
    df = get_weights_df()
    if not df.empty and target in df.index:
        # Get similarities for the target
        similarities = df.loc[target]
        # Filter: similarity > 0.3 (somewhat related) and < 0.8 (not too identical)
        valid_targets = similarities[(similarities > 0.3) & (similarities < 0.8)].index.tolist()
        
        if len(valid_targets) >= 4:
            return random.sample(valid_targets, 4)
            
    # Fallback to original SQL regex/string filtering if semantic selection fails
    cleaned_target = re.sub(r"s\b", "", target, flags=re.IGNORECASE)
    words = re.split(r"[\s/]+", cleaned_target)
    conditions = []
    params = []
    for word in words:
        if len(word) > 2:
            conditions.append("(target NOT LIKE ? AND ? NOT LIKE '%' || target || '%')")
            params.extend([f"%{word}%", word])
    
    if not conditions:
        conditions.append("(target NOT LIKE ? AND ? NOT LIKE '%' || target || '%')")
        params.extend([f"%{cleaned_target}%", cleaned_target])
        
    where_clause = " AND ".join(conditions)
    command = f"""
        SELECT DISTINCT target 
        FROM slurs 
        WHERE {where_clause} 
        ORDER BY RANDOM() 
        LIMIT 4;
    """
    return connect(command, params=tuple(params), multiple_lines=True)

def assemble_question(slur, other_targets):
    slur_word, correct_target, origin = slur

    targets = [correct_target, *other_targets]
    random.shuffle(targets)
    return {
        "slur": slur_word,
        "correct_target": correct_target,
        "targets": targets,
        "origin": origin,
    }

def ask_question(question):
    slur_word, correct_target, targets, origin = question.values()
    print(f"Which ethnic group does {slur_word} target?\nHint: it's {correct_target}")

    for index, target in enumerate(targets, start=1):
        print(f"{index}. {target}")

    while True:
        try:
            answer_idx = int(input("Enter a number: ")) - 1
            if 0 <= answer_idx < len(targets):
                break
            print("Please select a valid option from the list.")
        except ValueError:
            print("Please enter a valid number.")

    if targets[answer_idx] == correct_target:
        print(
            f"\nCorrect! {slur_word} refers to {correct_target}\n\nOrigins:\n{origin}"
        )
    else:
        print(f"\nIncorrect! {slur_word} refers to {correct_target}\n")

def debug_targets():
    debug_list = []
    regex = re.compile(r"\w+(?=s$)")
    general_targets = get_targets()
    replaced = []
    for i in range(10000):
        slur = generate_slur()
        other_targets = generate_other_targets(slur)
        debug_list.append([slur[0], slur[1], other_targets])
    df = pd.DataFrame(debug_list, columns=["Slur", "Correct Target", "Targets"])
    df.to_csv(DATA_DIR / "debug.csv", index=False)
