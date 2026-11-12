# Fe Builders Challenge submission checklist

## Pitch

FairGrant is an effect-free Fe library and native CLI that computes capped,
weighted integer budget allocations with explicit rounding and unallocated
balances, tested against an independent exact-rational oracle. A local CSV-to-HTML
review workflow makes recipient explanations and budget-increase anomalies visible
before a committee approves distribution. All scenario allocations run in Fe.

## Technical highlight

The allocation core declares no effects. Bounded u128/u64 inputs widen to u256
before arithmetic and use checked narrowing. One Fe implementation runs on both
EVM and native test backends and powers the native CLI. Typed shape errors prevent
silent truncation of recipient arrays.

## Scope

A working, tested developer-tool prototype. No financial transfers, wallet
integration, public deployment or production audit. At most 16 recipients.
Largest-remainder rounding is not budget-monotone and canonical order is the
caller's responsibility. These limitations are documented with a regression
counterexample, not suppressed.

## Reproduce

Use Fe 26.5.0 (3dab95f) and follow README.md. Run the commands in
scripts/check.sh, then scripts/demo.sh. Python verifies the Fe executable and adapts CSV/HTML I/O without duplicating the
allocation algorithm. Run `scripts/report.py` on the fictional examples to see
a grant review and a concrete budget-monotonicity failure.

## Entry evidence

- License: Apache-2.0.
- Core manifest: fe.toml. CLI manifest: cli/fe.toml.
- Tests: src/tests.fe and src/vectors.fe; scripts/verify.py and scripts/test_report.py.
- Explanation and bounds: docs/ALGORITHM.md.
- Results and limitations: docs/VERIFICATION.md.
- Human-facing explanation: docs/WALKTHROUGH.zh-CN.md.
- AI and reuse disclosure: README.md.

The exact final repository commit must be taken from GitHub after publishing;
do not substitute an unpushed local hash. Personal entry identifiers, contact
email and private submission codes are intentionally excluded from this file.
