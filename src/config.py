from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"
STATIC_DIR = ROOT_DIR / "static"
TEMPLATES_DIR = ROOT_DIR / "templates"

# Define shared files
SLURS_DB = DATA_DIR / "slurs.db"

DATA_DIR.mkdir(exist_ok=True)

MIN_SEMANTIC_SIMILARITY = 0.3
MAX_SEMANTIC_SIMILARITY = 0.8
SQLALCHEMY_DATABASE_URI = f"sqlite:///{SLURS_DB}"
