# slurdletwo

### _it's back now with 200% more slurs_

a flask app that creates an endless trivia quiz on slurs. you guess which ethnic or demographic group a slur targets. you can probably use this to do data science or something.

> **Heads up:** This project deals with slurs and offensive language by design. It's a game about understanding the targets of hate speech, not promoting it.

---

## how it works

1. A random slur is fetched from the database and displayed.
2. Four distractor targets are selected using semantic cosine similarity (MPNet embeddings), so the wrong answers are actually tricky (we finally figured out how to teach a computer that _albanian_ and _balkan_ are semantically similar words).
3. You pick one of the five shuffled options.
4. The result is revealed with the word's origin.

---

## the stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14+, Flask, Flask-SQLAlchemy |
| Database | SQLite (via SQLAlchemy ORM) |
| ML / Embeddings | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` |
| Frontend | Jinja2 templates, TailwindCSS v4 |
| Package management | `uv` (Python), `yarn` (Node) |
| Code quality | `ruff` (lint/format), `pyrefly` (type checking) |

---

## what goes where

```
slurdletwo/
├── app.py                  # Flask app factory, routes, session handling
├── main.py                 # CLI entry point (--init, --weights, --run, etc.)
├── src/
│   ├── config.py           # Centralised paths and constants
│   ├── models.py           # SQLAlchemy Slur model
│   ├── repository.py       # Data access layer (queries)
│   ├── slurs.py            # Game logic: assemble_question, get_other_targets
│   ├── ml_service.py       # TargetSimilarityService singleton
│   ├── weights.py          # MPNet embedding + similarity matrix generation
│   └── pull.py             # Scraper and ETL pipeline
├── templates/
│   ├── base.jinja          # Base layout
│   └── index.jinja         # Game UI
├── static/
│   ├── app.js              # Client-side guess handling
│   ├── src/input.css       # TailwindCSS source
│   └── css/style.css       # Compiled CSS (generated)
├── tests/                  # pytest test suite
│   ├── conftest.py         # Shared fixtures and SlurRecordStub factory
│   ├── test_app.py         # Flask route tests
│   ├── test_slurs.py       # Game logic tests
│   ├── test_repository.py  # Data access layer tests
│   ├── test_ml_service.py  # ML service tests
│   └── test_config.py      # Configuration invariant tests
├── data/                   # SQLite DB and generated weight CSVs (gitignored)
├── pyproject.toml          # Python project config (uv, ruff, pyrefly, pytest)
└── package.json            # Node scripts (TailwindCSS build/watch)
```

---

## how to run it

### Prerequisites

- Python 3.14+
- [`uv`](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [`yarn`](https://yarnpkg.com/) — `npm install -g yarn` (for CSS compilation only)

### 1. Install dependencies

`uv sync` should set it up. There is a `requirements.txt` too whatever floats your boat.
You'll also need node modules for Tailwind:
```bash
yarn install
```

### 2. Build the CSS

```bash
yarn build
```

Or watch for changes during development:

```bash
yarn watch
```

### 3. Initialise the database

This pulls the list of racial slurs from [the racial slur database](http://rsdb.org/) and pops them in an sqlite3 db + makes some csv files.

```bash
uv run python main.py --init
```

`--refresh` does this but deletes the generated files first.

### 4. Generate the similarity weights

This generates a csv with weights for each slur target using HuggingFace sentence transformer models. This runs MPNet over all unique targets and saves a cosine-similarity matrix so we can pick good distractors:

```bash
uv run python main.py --weights
```

> This step requires a GPU or patience — it takes a few minutes on CPU.

### 5. Run the app

```bash
uv run python main.py --run
```

The dev server starts at **http://localhost:5001**.

---

## CLI cheat sheet

| Flag | Description |
|---|---|
| `--init` | Scrape, parse, and load the database |
| `--refresh` | Like `--init` but cleans `data/` first |
| `--weights` | Generate the MPNet similarity matrix CSV |
| `--qa-weights [path]` | Print the top-25, middle-10, and bottom-10 target pairs for visual QA. Defaults to the MPNet CSV. |
| `--run` | Start the Flask development server on port 5001 |

---

## under the hood (distractor selection)

We used to just use regex to make sure the user isn't presented with targets that are too similar i.e. _asian_ and _asian/american_. Now we're fancy:

1. **Embedding**: All unique target labels (e.g. "Australians", "Mexicans") are encoded with `paraphrase-multilingual-mpnet-base-v2`.
2. **Matrix**: Pairwise cosine similarities are stored as a CSV at startup.
3. **Runtime**: For a given correct target, `TargetSimilarityService` fetches all targets with similarity in the range `(0.3, 0.8)` — related enough to be tricky, distinct enough not to be ambiguous — then samples 4 at random.
4. **Fallback**: If the target is missing from the matrix or has fewer than 4 valid neighbours, it falls back to the old regex/SQL `NOT LIKE` query to pick targets that don't share word stems with the correct answer.

We threw an LLM-as-a-Judge at this and it gave us a **47% valid distractor rate**, which is surprisingly good for slur target semantic groupings.

---

## development stuff

### Running tests

```bash
uv run pytest
```

```bash
uv run pytest -v          # verbose output
uv run pytest --tb=short  # compact tracebacks
```

There are **62 tests** because code quality matters even when you're writing a slur quiz.

### Type checking

```bash
uv run pyrefly check .
```

### Linting

```bash
uv run ruff check .
uv run ruff check --fix .   # auto-fix safe issues
```

> `LOG015` (root logger usage) warnings in `main.py` and `src/pull.py` are accepted and can be ignored.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FLASK_SECRET_KEY` | Random bytes (ephemeral) | Signs the session cookie. Set a stable value if you deploy this somewhere. |

---

## architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for a full breakdown of the component design, data flow, and refactoring notes.
