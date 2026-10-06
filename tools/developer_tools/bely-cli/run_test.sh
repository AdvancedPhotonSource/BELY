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
$RUNNER bely-cli auth login -h | grep -q -- --format
$RUNNER bely-cli auth logout -h | grep -q -- --format
$RUNNER bely-cli auth verify -h | grep -q -- --format
$RUNNER bely-cli entry attachment add -h | grep -q -- --format
$RUNNER bely-cli entry attachment list -h | grep -q -- --format
$RUNNER bely-cli entry attachment ls -h | grep -q -- --format
$RUNNER bely-cli doc delete -h | grep -q -- --force
$RUNNER bely-cli doc rm -h | grep -q -- --yes
$RUNNER bely-cli entry delete -h | grep -q -- --yes
$RUNNER bely-cli entry rm -h | grep -q -- --id
$RUNNER bely-cli entry attachment delete -h | grep -q -- --attachment-id
$RUNNER bely-cli entry attachment rm -h | grep -q -- --yes
$RUNNER bely-cli tui lookup -h | grep -q -- --format
$RUNNER bely-cli shell -h | grep -q -- cache
$RUNNER bely-cli shell init -h | grep -q -- --shell
$RUNNER bely-cli shell cache -h | grep -q -- refresh
_BELY_CLI_COMPLETE=bash_source $RUNNER bely-cli | grep -q '_bely_cli_completion'
_BELY_CLI_COMPLETE=zsh_source $RUNNER bely-cli | grep -q '_bely_cli_completion'
# Bare `tui` is the one group that carries --limit/--format itself (see CLAUDE.md).
$RUNNER bely-cli tui -h | grep -q -- --limit
