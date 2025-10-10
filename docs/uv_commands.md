# Recommended per-project workflow

uv init              # create pyproject.toml
uv venv              # create .venv here (optional; uv can prompt later)
uv add fastapi pydantic  # adds to pyproject + installs into .venv
uv run python -m fastapi --version  # runs using this project's .venv
uv sync              # (later) recreate env exactly from lockfile on new machines
