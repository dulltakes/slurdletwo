from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"
STATIC_DIR = ROOT_DIR / "static"
TEMPLATES_DIR = ROOT_DIR / "templates"

# Define shared files
SLURS_DB = DATA_DIR / "slurs.db"

DATA_DIR.mkdir(exist_ok=True)
