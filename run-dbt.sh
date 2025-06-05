#!/bin/bash

export PYTHONUTF8=1   # ← Force UTF-8 encoding for Python
set -o allexport
source .env
set +o allexport

# Load env vars from .env
set -o allexport
source .env
set +o allexport

# Run dbt with whatever arguments you pass in
dbt "$@"
