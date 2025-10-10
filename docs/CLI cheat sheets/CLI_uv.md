# 🐍 UV Cheat Sheet
A quick reference for using **uv** as a fast replacement for `pip`, `venv`, and other Python CLI tasks.

uv init                 # Initialize a new project (creates pyproject.toml + uv.lock)
uv add requests         # Add runtime dependencies
uv add polars faker
uv add --dev pytest     # Add dev-only dependencies

# Remove a package

## ▶️ Running Code ==============================================

# Run a script (no venv activation needed)
uv run python main.py

# Run a one-liner
uv run python -c "import requests; print('works!')"

## 🔄 Sync & Upgrades ===========================================

# Install packages from pyproject.toml / uv.lock
uv sync

# Upgrade to latest allowed versions
uv sync --upgrade

## 🔍 Inspect Environment =======================================

# List installed packages
uv pip list

# Show dependency tree
uv tree

## 📤 Export ====================================================

# Export pinned requirements (for CI or sharing)
uv pip freeze > requirements.txt

## ✅ Quick Workflow Example ====================================

uv init
uv add requests polars faker
uv add --dev pytest
uv run python main.py

### Notes =======================================================

* Keep `pyproject.toml` + `uv.lock` under version control.
* Don’t commit `.venv/` folders.
* Always run `uv sync` after pulling changes.
