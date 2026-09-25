import random
import re

import pandas as pd

from src.config import DATA_DIR
from src.ml_service import ml_service
from src.repository import (
    get_all_unique_targets,
    get_random_slur_record,
    get_targets_excluding_substrings,
)


def get_other_targets(slur_record):
    target = slur_record.target
    
    # Try semantic selection first
    similar_targets = ml_service.get_similar_targets(target, count=4)
    if similar_targets:
        return similar_targets
            
    # Fallback to SQL regex/string filtering if semantic selection fails
    return get_targets_excluding_substrings(target, limit=4)

def assemble_question(slur_record, other_targets):
    correct_target = slur_record.target

    targets = [correct_target, *other_targets]
    random.shuffle(targets)
    return {
        "slur": slur_record.slur,
        "correct_target": correct_target,
        "targets": targets,
        "origin": slur_record.origins,
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
    for i in range(10000):
        slur_record = get_random_slur_record()
        if not slur_record:
            continue
        other_targets = get_other_targets(slur_record)
        debug_list.append([slur_record.slur, slur_record.target, other_targets])
    df = pd.DataFrame(debug_list, columns=["Slur", "Correct Target", "Targets"])
    df.to_csv(DATA_DIR / "debug.csv", index=False)
