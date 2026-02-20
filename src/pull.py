import logging
import sqlite3
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Import all needed paths from config
from src.config import DATA_DIR, SLURS_DB

# Keep the intermediate files local to this script
SLURS_PATH = DATA_DIR / "slurs.html"
SLURS_CSV = DATA_DIR / "slurs.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("py_log.log", mode="w"), logging.StreamHandler()],
)


def clean_data_dir():
    logging.info("Cleaning data directory...")
    # Use the local variables and the imported config variable
    SLURS_PATH.unlink(missing_ok=True)
    SLURS_CSV.unlink(missing_ok=True)
    SLURS_DB.unlink(missing_ok=True)
    logging.info("Data directory cleaned successfully...")


def get_slurs():
    if SLURS_PATH.is_file():
        logging.info("We got slurs at home")
        return
    logging.info("Fetching slurs...")
    res = requests.get("http://www.rsdb.org/full")
    res.raise_for_status()

    res.encoding = "utf-8"

    logging.info("Download complete. Parsing HTML...")
    soup = BeautifulSoup(res.text, "html.parser")

    table_div = soup.find(attrs={"id": "slurs"})
    if table_div:
        table = table_div.find("table")
        SLURS_PATH.write_text(str(table), encoding="utf-8")
        logging.info(f"Table saved successfully to {SLURS_PATH}")
    else:
        logging.error("Could not find the target table in the HTML.")


def create_dataframe():
    logging.info("Loading HTML into DataFrame...")
    html_content = SLURS_PATH.read_text(encoding="utf-8")
    df_list = pd.read_html(StringIO(html_content))

    df = df_list[0]
    df.columns = ["slur", "target", "origins"]
    df.to_csv(SLURS_CSV, index=False, encoding="utf-8")
    logging.info(f"CSV saved successfully to {SLURS_CSV}")
    return df


def create_db(df):
    logging.info("Loading DataFrame into SQLite3 db...")
    # Use the imported SLURS_DB directly
    conn = sqlite3.connect(SLURS_DB)
    df.to_sql("slurs", conn, index=False, if_exists="replace")
    conn.close()
