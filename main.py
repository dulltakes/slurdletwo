import argparse
import logging
import os

from app import app
from src.pull import clean_data_dir, create_dataframe, create_db, get_slurs
from src.slurs import (
    assemble_question,
    generate_other_targets,
    generate_slur,
)
from src.weights import generate_similarity_weights

parser = argparse.ArgumentParser()
parser.add_argument("--init", help="Initialise database", action="store_true")
parser.add_argument("--refresh", help="Refresh database", action="store_true")
parser.add_argument("--run", help="Run app", action="store_true")
parser.add_argument("--slurs", help="Generate slurs", action="store_true")
parser.add_argument("--weights", help="Generate weights", action="store_true")


args = parser.parse_args()


def make_question():
    slur = generate_slur()
    other_targets = generate_other_targets(slur)
    return assemble_question(slur, other_targets)


if __name__ == "__main__":
    if args.refresh:
        args.init = True
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        if args.init:
            if args.refresh:
                clean_data_dir()

            get_slurs()
            df = create_dataframe()
            create_db(df)
            logging.info("Database initialization fully complete.")
    if args.slurs:
        print(make_question())
    if args.weights:
        generate_similarity_weights()
    if args.run:
        logging.info("Starting the Flask server...")
        app.config["DATA"] = make_question()
        app.config["MAKE_QUESTION"] = make_question
        app.run(debug=True, port=5001)
