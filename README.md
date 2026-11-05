# slurdletwo

### _it's back now with 200% more slurs_

a flask app that creates an endless trivia quiz on slurs. you guess which ethnic or demographic group a slur targets. you can probably use this to do data science or something.

> **Heads up:** This project deals with slurs and offensive language by design. It's a game about understanding the targets of hate speech, not promoting it.

---

## how it works

1. A random slur is fetched from the database and displayed.
2. Four distractor targets are selected using semantic similarity (TypeSafe Jev probabilities or MPNet embeddings), so the wrong answers are actually tricky (we finally figured out how to teach a computer that _albanian_ and _balkan_ are semantically similar words without accidentally thinking *guamanians* and *guatemalans* are the same thing).
3. You pick one of the five shuffled options.
4. The result is revealed with the word's origin.

---

## the stack

| Layer              | Technology                                                                |
| ------------------ | ------------------------------------------------------------------------- |
| Backend            | Python 3.14+, Flask, Flask-SQLAlchemy                                     |
| Database           | SQLite (via SQLAlchemy ORM)                                               |
| ML / Embeddings    | TypeSafe AI (Jev System One), `sentence-transformers` (MPNet)             |
| Frontend           | Jinja2 templates, TailwindCSS v4                                          |
| Package management | `uv` (Python), `yarn` (Node)                                              |
| Code quality       | `ruff` (lint/format), `pyrefly` (type checking)                          |

---

## what goes where

```
slurdletwo/
├── src/
│   └── slurdletwo/             # Modern PEP 517/621 uv package layout
│       ├── __init__.py         # Application factory (create_app)
│       ├── cli.py              # CLI dispatcher (registered as `slurdle`)
│       ├── config.py           # Centralised paths, configs, and thresholds
│       ├── extensions.py       # Decoupled extensions (SQLAlchemy db)
│       ├── models.py           # SQLAlchemy Slur model
│       ├── repository.py       # Data access layer (queries & class damping)
│       ├── pull.py             # Scraper and ETL pipeline
│       ├── game.py             # Game logic: assemble_question, get_other_targets
│       ├── ml/                 # Similarity & weight generation submodules
│       │   ├── __init__.py     # Exports ml_service singleton
│       │   ├── service.py      # Runtime TargetSimilarityService
│       │   ├── jev.py          # TypeSafe Jev System One probability generation
│       │   └── mpnet.py        # Offline MPNet embedding generation
│       ├── blueprints/         # Modular route blueprints
│       │   └── game/
│       │       ├── __init__.py # Blueprint definition
│       │       └── routes.py   # /, /next, /guess endpoints
│       ├── static/             # Static assets bundled within the package
│       │   ├── src/            # TailwindCSS input.css & TypeScript app.ts
│       │   ├── css/style.css   # Compiled CSS
│       │   └── app.js          # Compiled client JS bundle
│       └── templates/          # Jinja2 templates bundled within the package
│           ├── base.jinja      # Base layout
│           └── index.jinja     # Game UI
├── tests/                      # pytest test suite
│   ├── conftest.py             # App factory fixtures & test client
│   ├── test_factory.py         # Application factory tests
│   ├── test_app.py             # Route & HTTP behaviour tests
│   ├── test_jev_weights.py     # Jev weights pipeline tests
│   ├── test_slurs.py           # Game logic tests
│   ├── test_repository.py      # Data access layer tests
│   ├── test_ml_service.py      # ML service tests
│   └── test_config.py          # Configuration invariant tests
├── data/                       # SQLite DB and generated weight CSVs (gitignored)
├── pyproject.toml              # Python project config (uv, hatchling, ruff, pyrefly)
└── package.json                # Node scripts (TailwindCSS build/watch)
```

---

## how to run it

### Prerequisites

- Python 3.14+
- [`uv`](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [`yarn`](https://yarnpkg.com/) — `npm install -g yarn` (for CSS compilation only)

### 1. Install dependencies

`uv sync` installs the Python environment and registers `slurdle` in editable mode.
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
uv run slurdle --init
```

`--refresh` does this but deletes the generated files first.

### 4. Generate the similarity weights

We have two ways to generate the similarity weights matrix that powers distractor selection:

#### Option A: TypeSafe Jev (Recommended)
Uses TypeSafe AI's System One decision model (Jev) via OpenRouter to evaluate cultural and demographic relationships directly. It outputs calibrated probabilities ($0.0$ to $1.0$), avoids goofy subword traps (looking at you, *Guamanians* $\leftrightarrow$ *Guatemalans*), and won't pair fictional Cardassians with real people:

```bash
export OPENROUTER_API_KEY="your-key-here"
uv run slurdle --jev-weights
```

> Batches requests, checkpoints progress to `data/jev_weights_checkpoint.json` automatically, and resumes seamlessly if interrupted.

#### Option B: Offline MPNet Embeddings
Generates cosine similarities using HuggingFace's `paraphrase-multilingual-mpnet-base-v2` locally without an API key:

```bash
uv run slurdle --weights
```

> This step requires a GPU or patience — it takes a few minutes on CPU.

### 5. Run the app

```bash
uv run slurdle --run
```

The dev server starts at **http://localhost:5001**.

---

## CLI cheat sheet

All commands run through `uv run slurdle [FLAG]`:

| Flag                  | Description                                                                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `--init`              | Scrape, parse, and load the database                                                                               |
| `--refresh`           | Like `--init` but cleans `data/` first                                                                             |
| `--jev-weights`       | Generate weights using TypeSafe Jev via OpenRouter (calibrated probabilities, requires `OPENROUTER_API_KEY`)        |
| `--weights`           | Generate the MPNet similarity matrix CSV using local embeddings                                                    |
| `--qa-weights [path]` | Print top-25, middle-10, bottom-10 pairs and corridor stats. Defaults to Jev CSV if found, otherwise the MPNet CSV.|
| `--run`               | Start the Flask development server on port 5001                                                                    |

---

## under the hood (distractor selection)

We used to just use regex to make sure the user isn't presented with targets that are too similar i.e. _asian_ and _asian/american_. Now we're fancy:

1. **Similarity Matrix**: We precompute demographic relatedness across all unique target labels. We support two backends:
   - **TypeSafe Jev** (our preferred default): A System One probability model queried via OpenRouter. Because it evaluates semantic/cultural connection rather than raw character tokens, it won't pair *Guamanians* with *Guatemalans* just because they both start with "Gua-".
   - **MPNet Embeddings**: Dense 768-dimensional vectors from `paraphrase-multilingual-mpnet-base-v2` compared via cosine similarity.
2. **Corridor Filtering**: For a given correct target, `TargetSimilarityService` looks for candidates inside the semantic corridor `(0.3, 0.8)` — related enough to be tricky, distinct enough not to be ambiguous — then samples 4 at random.
3. **Fallback**: If the target is missing from the matrix or has fewer than 4 valid neighbours (like *Cardassians*, which Jev rightfully refuses to pair with real human ethnic groups), it falls back to the SQL `NOT LIKE` query to pick targets that don't share word stems with the correct answer.

When we benchmarked Jev vs MPNet, Jev kept **77.9%** of completely unrelated groups safely below the corridor while giving **99.3%** of real targets at least 4 viable, culturally grounded distractors.

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

There are **77 tests** because code quality matters even when you're writing a slur quiz.

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

| Variable             | Default                  | Description                                                                       |
| -------------------- | ------------------------ | --------------------------------------------------------------------------------- |
| `FLASK_SECRET_KEY`   | Random bytes (ephemeral) | Signs the session cookie. Set a stable value if you deploy this somewhere.        |
| `OPENROUTER_API_KEY` | `''`                     | OpenRouter API key used by TypeSafe Jev to generate calibrated similarity weights. |

---

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for a full breakdown of the component design, data flow, and refactoring notes.
