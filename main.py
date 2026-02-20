import argparse
import logging
import os

from app import app
from src.pull import clean_data_dir, create_dataframe, create_db, get_slurs
from src.slurs import (
    assemble_question,
    generate_other_targets,
    generate_slur,
    get_targets,
)

parser = argparse.ArgumentParser()
parser.add_argument("--init", help="Initialise database", action="store_true")
parser.add_argument("--refresh", help="Refresh database", action="store_true")
parser.add_argument("--run", help="Run app", action="store_true")
parser.add_argument("--slurs", help="Generate slurs", action="store_true")

args = parser.parse_args()

if __name__ == "__main__":
    if args.refresh:
        args.init = True

    # THE FIX: Only run the database logic if we are in the main process
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        if args.init:
            if args.refresh:
                clean_data_dir()

            get_slurs()
            df = create_dataframe()
            create_db(df)
            logging.info("Database initialization fully complete.")

    if args.run:
        logging.info("Starting the Flask server...")
        app.run(debug=True, port=5001)
    if args.slurs:
        targets = get_targets()
        slur = generate_slur()
        other_targets = generate_other_targets(slur, targets)
        assemble_question(slur, other_targets)
        # print(f"Target slur: {slur}\nOther slurs: {other_targets}")
