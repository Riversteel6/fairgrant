#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
fe --version
fe fmt --check
fe fmt cli --check
fe test
fe test --backend native
fe build cli --backend native --emit executable
python3 scripts/verify.py
python3 scripts/test_report.py
