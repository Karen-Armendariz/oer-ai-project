#!/bin/bash
# Setup script for OER AI Project

echo "--- Initializing Setup ---"

# 1. Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    /opt/homebrew/bin/python3 -m venv .venv
fi

# 2. Install dependencies
echo "Installing requirements..."
./.venv/bin/pip install -r backend/requirements.txt

# 3. Install Playwright browsers
echo "Installing Playwright Chromium engine..."
./.venv/bin/playwright install chromium

# 4. Make execution scripts executable
chmod +x run_*.sh 2>/dev/null || true

echo "--- Setup Complete ---"
echo "Run tests:  ./run_tests.sh"
echo "Run API:    ./run_api.sh"
echo "Scrapers:   ./run_search.sh  or  ./run_ingest.sh"
