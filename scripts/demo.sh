#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bin=./cli/out/fairgrant_cli
printf '\nChained caps: budget 10, weights 6/3/1, caps 3/4/10\n'
"$bin" 10 6 3 3 4 1 10
printf '\nRounding tie: budget 10, equal weights, precommitted order\n'
"$bin" 10 1 10 1 10 1 10
printf '\nInsufficient eligible capacity: zero weight cannot receive excess\n'
"$bin" 100 1 3 0 100 2 4
printf '\nDocumented Hamilton limitation: compare budget 25 with 26\n'
"$bin" 25 1500 100 1500 100 900 100 500 100 500 100 200 100
"$bin" 26 1500 100 1500 100 900 100 500 100 500 100 200 100
