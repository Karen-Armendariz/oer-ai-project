#!/bin/bash
# Run the ingestion script from the project root

# Get the absolute path of this script's directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_ROOT"

# Use the virtual environment's python
echo "--- Starting Ingestion Script ---"
./.venv/bin/python3 backend/ingest_data.py
