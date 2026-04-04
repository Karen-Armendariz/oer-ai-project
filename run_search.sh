#!/bin/bash
# Run the search script from the project root

# Get the absolute path of this script's directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_ROOT"

# Use the virtual environment's python
echo "--- Starting Search Script ---"
./.venv/bin/python3 backend/search_syllabus.py
