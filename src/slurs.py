import random
import sqlite3

import pandas as pd

from src.config import DATA_DIR, SLURS_DB


def connect(command, multiple_lines=False):
    try:
        conn = sqlite3.connect(SLURS_DB)
        cursor = conn.cursor()
        cursor.execute(command)
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


import re


def generate_other_targets(slur):
    cleaned_target = re.sub(r"s\b", "", slur[1], flags=re.IGNORECASE)
    words = re.split(r"[\s/]+", cleaned_target)
    conditions = []
    for word in words:
        if len(word) > 2:
            conditions.append(
                f"(target NOT LIKE '%{word}%' AND '{word}' NOT LIKE '%' || target || '%')"
            )
    if not conditions:
        conditions.append(
            f"(target NOT LIKE '%{cleaned_target}%' AND '{cleaned_target}' NOT LIKE '%' || target || '%')"
        )
    where_clause = " AND ".join(conditions)
    command = f"""
        SELECT DISTINCT target 
        FROM slurs 
        WHERE {where_clause} 
        ORDER BY RANDOM() 
        LIMIT 4;
    """
    return connect(command, multiple_lines=True)


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
    # for target in general_targets:
    #     if re.match(regex, target):
    #         replaced.append([target, re.match(regex, target).group()])
    # print(replaced)
    df = pd.DataFrame(debug_list, columns=["Slur", "Correct Target", "Targets"])
    df.to_csv(DATA_DIR / "debug.csv", index=False)
    # df2 = pd.DataFrame(get_targets(), columns=["target"])
    # df2.to_csv(DATA_DIR / "targets.csv", index=False)
