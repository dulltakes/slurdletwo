# Agent Rules & Architecture for slurdletwo

## Project Context and Architecture
This is a Flask web application with a TailwindCSS frontend that serves a trivia game.
- **Backend**: Flask application (`app.py`, `main.py`) running on Python 3.14+.
- **Frontend**: Jinja2 templates with TailwindCSS (`package.json` scripts compile `static/src/input.css` to `static/css/style.css`).
- **ML/Data**: Uses `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` to embed target labels and build a cosine-similarity matrix for distractor selection. The `TargetSimilarityService` singleton in `src/ml_service.py` loads the precomputed CSV at startup.
- **Data Pipeline**: `src/pull.py` scrapes, parses, and loads slur data into SQLite via `pandas` and `BeautifulSoup`. The ORM layer is Flask-SQLAlchemy (`src/models.py`, `src/repository.py`).
- **Configuration**: All paths and thresholds are centralised in `src/config.py`.
- **Dependency Management**: Python dependencies are managed with `uv` (`pyproject.toml`, `uv.lock`). Node dependencies are managed with `yarn` (`package.json`, `yarn.lock`).
- **Code Quality**: `ruff` for linting/formatting, `pyrefly` for type checking (configured via `pyrightconfig.json`).

## CLI Reference (`main.py`)
- `--init`: Scrape, parse, and load the database.
- `--refresh`: Like `--init` but cleans the data directory first.
- `--weights`: Generate the MPNet similarity matrix CSV.
- `--qa-weights [path]`: Print top-25, middle-10, bottom-10 target pairs from a weights CSV.
- `--run`: Start the Flask dev server on port 5001.

## General Agent Rules
1. **Python Execution**: **Always** use `uv` if invoking Python or managing dependencies (e.g., `uv run python`, `uv add <pkg>`).
2. **Code Discoverability**: Write code that is easy to search for in plain text (meaningful, unique identifiers, descriptive error messages).
3. **Testing**: The test suite lives in `tests/` with a shared `conftest.py` providing fixtures (`app`, `client`, `app_context`, `SlurRecordStub`, factory). Run with `uv run pytest`. All new code should have corresponding tests.
4. **Type Safety**: Run `uv run pyrefly check .` before committing. The project uses `pyrightconfig.json` to set the import root to `.` (not `src/`).
5. **Linting**: Run `uv run ruff check .`. The remaining `LOG015` warnings (root logger usage) are accepted. All other rules must pass.

## Test Suite Structure
Tests are organised by module with pytest classes:
- `test_app.py` — Flask routes: rendering, session, correct/incorrect guesses, edge cases.
- `test_slurs.py` — Game logic: `assemble_question` structure/shuffling, `get_other_targets` integration.
- `test_repository.py` — Data access: random records, unique targets, substring exclusion.
- `test_ml_service.py` — ML service: init state, weight loading, threshold enforcement.
- `test_config.py` — Configuration: path invariants, threshold bounds, URI format.

## Skill Usage Contexts
Based on the installed skills in `.agents/skills` and plugins, use the following skills in these contexts:

### Core Development
- **`python-pro`**: Use for all backend Python development in `app.py`, `main.py`, `src/`, and `tests/`. Apply modern Python 3.14+ features, type hinting, pytest best practices, and performance optimizations.
- **`write-discoverable-code`**: Apply continuously when creating new functions, classes, variables, and error messages to ensure they are easily searchable via plain-text grep.
- **`uv-package-manager`**: Use for any Python dependency management (adding, removing, or syncing packages via `uv add`, `uv remove`, `uv sync`).

### Frontend
- **`frontend-developer`**: Use when modifying Jinja2 templates, updating `static/src/input.css`, or configuring TailwindCSS.
- **`tailwind-design-system`**: Use for building scalable UI components and establishing a consistent design language within TailwindCSS and HTML templates.
- **`modern-web-guidance`** *(plugin)*: Execute **first** for any HTML/CSS/client-side JS task. Covers modern layout APIs, scroll animations, performance (CWV), and browser APIs.
- **`chrome-extensions`** *(plugin)*: Use if building Chrome extension functionality (Manifest V3).

### ML & Data
- **`train-sentence-transformers`**: Use when fine-tuning or training sentence-transformer models. The project currently uses a **pretrained** MPNet model for embedding, not a fine-tuned one — this skill is relevant if the user wants to train a custom model for better distractor quality.
- **`hf-cli`**: Use for any Hugging Face Hub interaction — downloading models, uploading datasets, managing repos, browsing papers, or deploying inference endpoints. Trigger on mentions of `hf`, `huggingface`, or any HF ecosystem task.

### Documentation & Architecture
- **`docs-architect`**: Use proactively when documenting the system architecture, adding READMEs, or explaining the ML pipeline. Reference `ARCHITECTURE.md` as the canonical architecture document.
- **`python-development-python-scaffold`**: Use when scaffolding new major features, structuring new directories, or setting up new integrations.

### AI & Prompting
- **`prompt-engineer`**: Use when building AI features, crafting system prompts, or optimising LLM interactions (e.g., if reintroducing LLM-based QA or adding AI-powered features).
