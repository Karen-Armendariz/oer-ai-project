#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$PROJECT_ROOT"

if [ ! -x ".venv/bin/pytest" ]; then
  echo "pytest not found. Run ./setup.sh first."
  exit 1
fi

exec ./.venv/bin/pytest tests/ -v "$@"
