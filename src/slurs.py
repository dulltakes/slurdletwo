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
    command = f"""SELECT DISTINCT target FROM slurs WHERE target <> '{target_filter}' ORDER BY RANDOM() LIMIT 4;"""
    return connect(command, multiple_lines=True)


def assemble_question(slur, other_targets):
    targets = [slur[1], *other_targets]
    random.shuffle(targets)
    print(f"Which ethnic group does {slur[0]} target?\nHint: it's {slur[1]}")
    for index, target in enumerate(targets):
        print(f"{index + 1}. {target}")
    answer = input("Enter a number: ")
    if answer.isdigit():
        answer = int(answer)
        answer -= 1
        print("Targets:", targets[int(answer)])
        print("Index of correct answer:", targets.index(slur[1]))
        if targets[int(answer)] == targets[targets.index(slur[1])]:
            print(f"\nCorrect! {slur[0]} refers to {slur[1]}\n\nOrigins:\n{slur[2]}")
        else:
            print(f"\nIncorrect! {slur[0]} refers to {slur[1]}\n")
    else:
        answer = input("Please enter a number: ")
