#!/bin/bash
set -e

PYTHON=/C2/conda/envs/bely/bin/python

# COMPONENT_DIR is set by the test harness; default to this script's dir so the
# test is also runnable standalone.
COMPONENT_DIR="${COMPONENT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"

# Unit tests (run from the project dir so unittest discovers test/).
(cd "$COMPONENT_DIR" && "$PYTHON" -m unittest)

# Smoke test: the published command loads and the global --format option is wired.
bely.py -h > /dev/null
bely.py --format json doc -h > /dev/null
