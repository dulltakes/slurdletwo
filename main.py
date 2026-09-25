import argparse
import logging
import os

from app import app
from src.pull import clean_data_dir, create_dataframe, create_db, get_slurs
from src.weights import generate_similarity_weights

parser = argparse.ArgumentParser()
parser.add_argument("--init", help="Initialise database", action="store_true")
parser.add_argument("--refresh", help="Refresh database", action="store_true")
parser.add_argument("--run", help="Run app", action="store_true")
parser.add_argument("--weights", help="Generate weights", action="store_true")
parser.add_argument("--qa-weights", nargs='?', const="", help="QA the generated combined weights (optionally provide a CSV path)")

args = parser.parse_args()

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

    if args.weights:
        generate_similarity_weights()

    if args.qa_weights is not None:
        path = None if args.qa_weights == "" else args.qa_weights
        from src.weights import qa_weights
        qa_weights(path)

    if args.run:
        logging.info("Starting the Flask server...")
        app.run(debug=True, port=5001)
