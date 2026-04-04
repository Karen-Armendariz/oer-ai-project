#!/bin/bash
# Run the OER ingestion script from the project root

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_ROOT"

# Use project-local cache to avoid permission issues
export HF_HOME="$PROJECT_ROOT/.cache/huggingface"
export PYTHONPATH="$PROJECT_ROOT"

echo "--- Starting OER Ingestion Script ---"
./.venv/bin/python3 backend/ingest_oer.py
