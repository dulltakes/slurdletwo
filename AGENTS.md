# Agent Rules & Architecture for slurdletwo

## Project Context and Architecture
This is a Flask web application with a TailwindCSS frontend.
- **Backend**: Flask application (`app.py`, `main.py`) running on Python 3.14+.
- **Frontend**: HTML templates with TailwindCSS (`package.json` scripts compile `static/src/input.css` to `static/css/style.css`).
- **ML/Data**: The project relies on `pandas`, `scikit-learn`, and `sentence-transformers`, indicating NLP and data processing capabilities within the backend.
- **Dependency Management**: Python dependencies are managed with `uv` (`pyproject.toml`, `uv.lock`). Node dependencies are managed with `yarn` (`package.json`, `yarn.lock`).

## General Agent Rules
1. **Python Execution**: **Always** use `uv` if invoking Python or managing dependencies (e.g., `uv run python`, `uv add <pkg>`).
2. **Code Discoverability**: Write code that is easy to search for in plain text (meaningful, unique identifiers, descriptive error messages).

## Skill Usage Contexts
Based on the installed skills in `.agent/skills`, use the following skills in these contexts:

- **`uv-package-manager`**: Use for any Python dependency management (adding, removing, or syncing packages).
- **`python-pro`**: Use for general backend Python development in `app.py`, `main.py`, `src/`, and `tests/`. Apply modern Python features, type hinting, and performance optimizations.
- **`frontend-developer`**: Use when modifying templates, updating `static/src/input.css`, or configuring TailwindCSS.
- **`tailwind-design-system`**: Use for building scalable UI components and establishing a consistent design language within TailwindCSS and HTML templates.
- **`write-discoverable-code`**: Apply continuously when creating new functions, classes, variables, and error messages to ensure they are easily searchable.
- **`docs-architect`**: Use proactively when documenting the system architecture, adding robust READMEs, or explaining the ML pipeline.
- **`python-development-python-scaffold`**: Use when scaffolding new major features, structuring new directories, or setting up new integrations.
