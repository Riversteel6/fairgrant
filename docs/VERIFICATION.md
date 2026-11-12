# Verification record

Checked on x86-64 Linux with Fe **26.5.0 (3dab95f)** during the contest window,
November 12, 2026. These are local test results, not an external audit or remote
CI claim. Re-run `bash scripts/check.sh` against the commit you are reviewing.

| Check | Result |
|---|---|
| Fe formatting for library and CLI | Passed |
| Sonatina/EVM unit and fixture suite | 133 passed, 0 failed |
| Native unit and fixture suite | 133 passed, 0 failed |
| Native CLI build | Passed |
| Default exact-rational comparison | 2,010 valid cases + 10 malformed inputs passed |
| Extended exact-rational comparison | 10,010 valid cases + 10 malformed inputs passed |

## What is covered

128 deterministic exact-rational fixtures cover ordinary amounts, chained caps,
all-zero weights, zero caps, zero budget, insufficient capacity, tied remainders,
16 recipients, u128/u64 maxima, and the Hamilton budget paradox. Handwritten
regressions cover typed shape errors, nonzero padding, stable tie resolution and
weight-scale invariance. The Python harness additionally checks exact cap/rounding
flags, conservation, eligibility, cap bounds and floor/ceiling proximity.

The reference implementation uses Python `Fraction` and sorted cap/weight
breakpoints. Fe uses sequential cap elimination with integer cross products.
This structural difference reduces, but cannot eliminate, shared-specification
errors. Seed: 20261112. There is no random live network input.

## Reproduce extended checks

```sh
fe build cli --backend native --emit executable
python3 scripts/verify.py --cases 10000
```

The accepted decimal format permits leading zeroes. Signs, whitespace, decimal
points, hexadecimal notation and non-ASCII digits are rejected. Budgets/caps are
bounded by u128 and weights by u64. The test harness enforces per-process timeouts.

## Not verified or promised

No external security audit, mainnet deployment, gas benchmark, GUI, Windows
native build or cross-platform packaging is claimed. Payment handling,
authentication, sybil resistance and selecting trustworthy weights are outside
scope. The test oracle does not turn this into a proof of general fairness.

## Local review integration

`python3 scripts/test_report.py` runs six integration tests against the actual Fe binary: realistic CSV allocation, budget paradox alerts, HTML escaping and spreadsheet formula defense, malformed CSVs, full-u128 budget edges, exports and no-overwrite behavior. No browser calculations replace Fe.
