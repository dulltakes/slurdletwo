"""Command line interface dispatcher for Slurdle."""

import argparse
import logging
import os
import sys

from slurdletwo import create_app
from slurdletwo.pull import clean_data_dir, create_dataframe, create_db, get_slurs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Slurdle administrative CLI")
    parser.add_argument("--init", help="Initialise database", action="store_true")
    parser.add_argument("--refresh", help="Refresh database", action="store_true")
    parser.add_argument("--run", help="Run app", action="store_true")
    parser.add_argument(
        "--weights",
        help="Generate weights using sentence-transformers MPNet",
        action="store_true",
    )
    parser.add_argument(
        "--jev-weights",
        help="Generate weights using TypeSafe Jev via OpenRouter",
        action="store_true",
    )
    parser.add_argument(
        "--qa-weights",
        nargs="?",
        const="",
        help="QA the generated combined weights (optionally provide a CSV path)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.refresh:
        args.init = True

    if os.environ.get("WERKZEUG_RUN_MAIN") != "true" and args.init:
        if args.refresh:
            clean_data_dir()
        get_slurs()
        df = create_dataframe()
        create_db(df)
        logging.info("Database initialization fully complete.")

    if args.weights:
        from slurdletwo.ml.mpnet import generate_similarity_weights

        generate_similarity_weights()

    if args.jev_weights:
        from slurdletwo.ml.jev import generate_jev_weights

        generate_jev_weights()

    if args.qa_weights is not None:
        path = None if args.qa_weights == "" else args.qa_weights
        if path and "jev" in path.lower():
            from slurdletwo.ml.jev import qa_weights as qa_jev_weights

            qa_jev_weights(path)
        else:
            from slurdletwo.ml.mpnet import qa_weights

            qa_weights(path)

    if args.run:
        logging.info("Starting the Flask server...")
        app = create_app()
        app.run(debug=True, port=5001)

    return 0


if __name__ == "__main__":
    sys.exit(main())
