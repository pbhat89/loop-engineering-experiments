#!/usr/bin/env bash
# Thin wrapper; the logic lives in scripts/pipeline.py (Python equivalent).
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run python scripts/pipeline.py verify "$@"
