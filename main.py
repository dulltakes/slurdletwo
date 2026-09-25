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
parser.add_argument("--qa-llm", nargs='?', const="", help="Automated QA using Gemini LLM-as-a-Judge")
parser.add_argument("--qa-reranker", nargs='?', const="", help="Automated QA using CrossEncoder reranker")

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

    if args.qa_llm is not None:
        path = None if args.qa_llm == "" else args.qa_llm
        from src.weights import qa_weights_llm
        qa_weights_llm(path)

    if args.qa_reranker is not None:
        path = None if args.qa_reranker == "" else args.qa_reranker
        from src.weights import qa_weights_reranker
        qa_weights_reranker(path)

    if args.run:
        logging.info("Starting the Flask server...")
        app.run(debug=True, port=5001)
