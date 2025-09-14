#!/bin/sh
set -e

# Activate virtual environment and run the main script
source .venv/bin/activate
exec python src/check_pr_issue_action/main.py "$@"
