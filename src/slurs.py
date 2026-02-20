import random
import sqlite3

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


def generate_other_targets(slur, targets):
    target_filter = slur[1]
    command = f"""SELECT DISTINCT target FROM slurs WHERE target NOT LIKE '%{target_filter}%' AND '{target_filter}' NOT LIKE '%' || target || '%' ORDER BY RANDOM() LIMIT 4;"""
    return connect(command, multiple_lines=True)


def assemble_question(slur, other_targets):
    slur_word, correct_target, origin = slur

    targets = [correct_target, *other_targets]
    random.shuffle(targets)

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
