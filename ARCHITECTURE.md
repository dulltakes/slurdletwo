# System Architecture & Design

## Overview
**Slurdle** is a web-based trivia game built with a Python Flask backend and a TailwindCSS frontend. The application involves data scraping, data processing, and machine learning elements for semantic target selection.

## Components

### 1. Data Pipeline (`src/pull.py`)
- **Scraping**: Fetches the slur database from `rsdb.org/full` using `requests` and `BeautifulSoup`.
- **ETL (Extract, Transform, Load)**: 
  - Parses the HTML into a `pandas` DataFrame.
  - Cleans target names (e.g., standardizing pluralization and combining synonyms via `TARGET_CORRECTIONS`).
  - Dumps the cleaned data into an SQLite database (`data/slurs.db`).

### 2. Core Game Logic & ML (`src/slurs.py`, `src/weights.py`, `src/ml_service.py`)
- **Target Selection**: When generating a question, the game needs 1 correct answer and 4 incorrect choices.
- **Semantic Matching (MPNet)**: Distractors are selected based on the cosine similarity of the target labels embedded using `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`. This model's multilingual and paraphrase fine-tuning naturally clusters demographics, ethnicities, and geographic terms logically, providing an excellent 47% viable distractor rate as validated by LLM-as-a-Judge.
- **ML Service (`src/ml_service.py`)**: A `TargetSimilarityService` singleton loads the precomputed similarity matrix at startup and serves target lookups at runtime. Similarity results are filtered by configurable `MIN_SEMANTIC_SIMILARITY` / `MAX_SEMANTIC_SIMILARITY` thresholds (default 0.3–0.8).
- **Fallback Logic**: If semantic matching fails (target not in the matrix, or fewer than 4 valid neighbours), it falls back to string exclusion SQL queries to pick random targets that don't share substrings with the correct target.

### 3. Data Access Layer (`src/repository.py`, `src/models.py`)
- **ORM**: Flask-SQLAlchemy with a `Slur` model mapping the `slurs` table.
- **Queries**:
  - `get_random_slur_record()` — random single record via `ORDER BY RANDOM()`.
  - `get_all_unique_targets()` — deduplicated target list.
  - `get_targets_excluding_substrings(target, limit)` — fallback distractor query using parameterised `NOT LIKE` clauses split on word boundaries.

### 4. Configuration (`src/config.py`)
- Centralises all path constants (`DATA_DIR`, `SLURS_DB`, `STATIC_DIR`, `TEMPLATES_DIR`).
- Defines semantic similarity thresholds and the SQLAlchemy database URI.

### 5. Web Backend (`app.py`, `main.py`)
- **Web Server**: A lightweight Flask application.
- **State Management**: Uses Flask's signed cookie `session` to securely store the current question's correct target and origin between the initial page load and the guess submission.
- **Endpoints**:
  - `GET /`: Renders the main Jinja template (`index.jinja`) with a newly generated question.
  - `POST /guess`: Accepts a JSON payload containing the user's guess and evaluates it against the `session` state, returning a JSON response.
- **CLI** (`main.py`):
  - `--init` / `--refresh`: Scrape, parse, and load the database.
  - `--weights`: Generate the MPNet similarity matrix CSV.
  - `--qa-weights [path]`: Print the top-25, middle-10, and bottom-10 target pairs from a weights CSV for quick visual QA.
  - `--run`: Start the Flask development server.

### 6. Frontend
- **Templating**: Jinja2 (`templates/index.jinja`).
- **Styling**: TailwindCSS, managed via Yarn. Source CSS is in `static/src/input.css` and compiled to `static/css/style.css`.

---

## Test Suite

The project uses **pytest** with a shared `conftest.py` providing fixtures for the Flask test client, app context, and a `SlurRecordStub` factory. Tests are organised by module:

| Module | Coverage |
|---|---|
| `test_app.py` | Flask routes: index rendering, session population, correct/incorrect guesses, edge cases (expired session, empty body) |
| `test_slurs.py` | Game logic: `assemble_question` structure, shuffling, special characters; `get_other_targets` integration |
| `test_repository.py` | Data access: random records, unique targets, substring exclusion, slash-separated and short targets |
| `test_ml_service.py` | ML service: init state, weight loading, square matrix, threshold enforcement, unknown targets |
| `test_config.py` | Configuration: path relationships, threshold invariants, URI format |

---

## Discoverability & Refactoring Suggestions

Based on the `write-discoverable-code` guidelines, here are recommendations to improve the maintainability and searchability of the codebase:

### 1. Separate Data Access from Business Logic
Currently, `src/slurs.py` mixes direct SQL query execution (`connect`, hardcoded strings) with game logic (`assemble_question`). 
- **Action**: Extract all database interactions into a `src/repository.py` or `src/db.py` module. 
- **Why**: Makes it easier to search for "database queries" or "slur repository". Testing game logic becomes significantly easier if database calls are abstracted.

### 2. Rename Vague Identifiers
- `generate_slur()` -> `get_random_slur_record()`
- `get_targets()` -> `get_all_unique_targets()`
- `connect()` -> `execute_query()` or `fetch_from_db()`
- **Why**: "Generate" implies creation from scratch, while "get" or "fetch" correctly implies retrieval. Unique, descriptive names improve plain-text code searchability.

### 3. Centralize Configuration and Constants
- Hardcoded string values (like `target NOT LIKE ?`) and similarity thresholds (`> 0.3`, `< 0.8`) are buried in `src/slurs.py`.
- **Action**: Move thresholds to `src/config.py` (e.g., `MIN_SEMANTIC_SIMILARITY = 0.3`).
- **Why**: Magic numbers are hard to search for. Named constants are discoverable and self-documenting.

### 4. Manage Global State
- `WEIGHTS_DF` is a module-level global variable in `src/slurs.py`. 
- **Action**: Attach this loaded DataFrame to the Flask `app.config` or an application context (like a singleton ML service class).
- **Why**: Global variables can lead to subtle bugs and are hard to mock in testing.

### 5. Transition to an ORM (Optional but Recommended)
- Using SQLAlchemy or SQLModel instead of raw sqlite3 strings would make database schema and queries inherently more searchable. For example, `session.query(Slur)` is easier to navigate with IDE tools than a raw `"SELECT * FROM slurs"` string.
