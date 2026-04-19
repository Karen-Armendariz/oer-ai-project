#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_ROOT"

export HF_HOME="$PROJECT_ROOT/.cache/huggingface"
export PYTHONPATH="$PROJECT_ROOT"

./.venv/bin/uvicorn backend.api:app --host 0.0.0.0 --port 8000
