# Formatting Setup Guide

## Best Practice: Format Before Committing ✅

Yes, formatting before committing is best practice! It:
- Prevents CI failures
- Keeps code consistent
- Saves time (no re-commit cycles)

## Option 1: Pre-commit Hooks (Recommended) 🎯

**Automatic formatting before every commit** - no extra steps needed!

### Setup:
```bash
# Install pre-commit
uv sync --group dev

# Install git hooks
uv run pre-commit install

# Test it works
uv run pre-commit run --all-files
```

### How it works:
- Every time you run `git commit`, it automatically:
  1. Formats your code with Ruff
  2. Runs linting checks
  3. Only commits if everything passes

### If formatting changes files:
- The hook will auto-format and stage the changes
- You just need to commit again (the files are already formatted)

## Option 2: Manual Format Check (Backup) 🔧

### Quick Check (Windows):
```bash
scripts\format_check.bat
```

### Quick Check (Linux/Mac):
```bash
./scripts/format_check.sh
```

### Or manually:
```bash
# Check formatting
uv run ruff format --check .

# If it fails, auto-fix:
uv run ruff format .
```

## Option 3: IDE Integration (VS Code) 💻

Add to `.vscode/settings.json`:
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  }
}
```

This formats automatically when you save files!

## Recommendation

**Use Option 1 (Pre-commit hooks)** - it's automatic and you'll never forget!
