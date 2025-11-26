# Git Workflow: Merge to Main and Start New Branch

## Current Status
- **Current Branch**: `feat/kafka`
- **Target Branch**: `main`
- **Uncommitted Changes**: Yes

## Step-by-Step Instructions

### Step 1: Commit Current Changes

```bash
cd FANalyze_v2.0

# Check what files should be committed (skip .env, logs, target if they're in .gitignore)
git status

# Add all changes (or add specific files)
git add .

# Or add specific files only (recommended - skip .env, logs, target):
git add CAPSTONE_ASSESSMENT.md
git add airflow/
git add docker-compose-airflow.yml
git add docker-compose-kafka.yml
git add kafka/
git add docker-compose-demo.yml
git add docker-compose.yaml
git add pyproject.toml
git add uv.lock

# Commit with a descriptive message
git commit -m "feat: Add Kafka streaming pipeline and Airflow orchestration

- Add Kafka producer/consumer for ticket sales streaming
- Add Airflow docker-compose setup with DAGs
- Update all docker-compose files to use Asia/Bangkok timezone
- Update Airflow Dockerfile to use uv instead of pip
- Add pyproject.toml airflow optional dependencies
- Add comprehensive documentation"
```

### Step 2: Push Current Branch (Optional but Recommended)

```bash
# Push your current branch to remote (good practice before merging)
git push origin feat/kafka
```

### Step 3: Switch to Main Branch

```bash
# Switch to main branch
git checkout main

# Or if main doesn't exist locally:
# git checkout -b main origin/main
```

### Step 4: Pull Latest Changes from Main

```bash
# Make sure main is up to date
git pull origin main
```

### Step 5: Merge feat/kafka into Main

```bash
# Merge your feature branch into main
git merge feat/kafka

# If there are conflicts, resolve them, then:
# git add .
# git commit -m "Merge feat/kafka into main"
```

### Step 6: Push Main to Remote

```bash
# Push merged main to remote
git push origin main
```

### Step 7: Create and Switch to New Branch

```bash
# Create and switch to a new branch
git checkout -b feat/your-new-feature-name

# Or if you want a different naming convention:
# git checkout -b fix/your-fix-name
# git checkout -b chore/your-chore-name
```

### Step 8: Push New Branch (Optional)

```bash
# Push new branch to remote
git push -u origin feat/your-new-feature-name
```

## Quick One-Liner Version

If you want to do it all at once (after committing):

```bash
# After committing on feat/kafka:
git push origin feat/kafka && \
git checkout main && \
git pull origin main && \
git merge feat/kafka && \
git push origin main && \
git checkout -b feat/your-new-feature-name
```

## Important Notes

### Files to Exclude from Commit

Some files might be in `.gitignore` and shouldn't be committed:
- `.env` (contains secrets)
- `dbt/logs/` (generated logs)
- `dbt/target/` (generated files)

Check your `.gitignore` before committing:

```bash
cat .gitignore
```

### If You Have Conflicts

If merge conflicts occur:

```bash
# See conflicted files
git status

# Edit conflicted files, resolve conflicts
# Then:
git add <resolved-files>
git commit -m "Resolve merge conflicts"
```

### Alternative: Use Pull Request (Recommended for Teams)

If working with a team, consider using a Pull Request instead:

```bash
# After committing and pushing feat/kafka:
# 1. Go to GitHub/GitLab
# 2. Create Pull Request from feat/kafka to main
# 3. Review and merge via UI
# 4. Then locally:
git checkout main
git pull origin main
git checkout -b feat/your-new-feature-name
```

## Common Branch Naming Conventions

- `feat/` - New features
- `fix/` - Bug fixes
- `chore/` - Maintenance tasks
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding tests

Example: `feat/airflow-integration`, `fix/kafka-connection`, `chore/update-dependencies`

