#!/bin/bash
set -e

# COMPONENT_DIR is set by the test harness; default to this script's dir so the
# test is also runnable standalone.
COMPONENT_DIR="${COMPONENT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
cd "$COMPONENT_DIR"

# RUNNER lets a packaging harness drop back to a bare interpreter (RUNNER="")
# when it wants to exercise an already-installed bely-cli instead of the venv.
RUNNER="${RUNNER:-uv run}"

# Unit tests (run from the project dir so unittest discovers test/).
$RUNNER python -m unittest

# Smoke test: the published command loads and --format is wired per-command
# (appended to a leaf command, not at the top level).
$RUNNER bely-cli -h > /dev/null
$RUNNER bely-cli doc list -h | grep -q -- --format
$RUNNER bely-cli tui lookup -h | grep -q -- --format
