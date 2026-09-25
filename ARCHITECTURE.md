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

### 2. Core Game Logic & ML (`src/slurs.py`, `src/weights.py`)
- **Target Selection**: When generating a question, the game needs 1 correct answer and 4 incorrect choices.
- **Semantic Matching (MPNet Approach)**: Multiple-choice distractors are selected based on the cosine similarity of the target labels embedded using `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`. This model's multilingual and paraphrase fine-tuning naturally clusters demographics, ethnicities, and geographic terms highly logically, providing an excellent 47% viable distractor rate.
- **Fallback Logic**: If semantic matching fails, it falls back to string exclusion SQL queries to pick random targets that don't share substrings with the correct target.

### 3. Web Backend (`app.py`, `main.py`)
- **Web Server**: A lightweight Flask application.
- **State Management**: Uses Flask's signed cookie `session` to securely store the current question's correct target and origin between the initial page load and the guess submission.
- **Endpoints**:
  - `GET /`: Renders the main Jinja template (`index.jinja`) with a newly generated question.
  - `POST /guess`: Accepts a JSON payload containing the user's guess and evaluates it against the `session` state, returning a JSON response.

### 4. Frontend
- **Templating**: Jinja2 (`templates/index.jinja`).
- **Styling**: TailwindCSS, managed via Yarn. Source CSS is in `static/src/input.css` and compiled to `static/css/style.css`.

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
