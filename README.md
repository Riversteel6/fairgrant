# FairGrant

**A small, auditable Fe library for capped weighted integer allocation.**

Turn a budget, contribution weights and recipient caps into an exact allocation,
without losing rounding dust or giving excess funds to ineligible recipients.
The same Fe core runs in EVM tests and a native command-line tool. No wallet,
RPC, deposit, token or blockchain deployment is required.

This is an allocation **calculator**, not a payment contract. It never sends funds.
The algorithms are established; the contribution is the Fe implementation,
bounded API, explanation flags and reproducible cross-backend verification.

## Try it in two minutes

Requires x86-64 Linux (tested), Python 3.10+ for verification and Fe **26.5.0**
(`3dab95f`). Fe also supports other native hosts, but they are not verified here.
Install the pinned release using the [official guide](https://fe-lang.org/docs/guide/installation/):

```sh
curl -fsSL https://raw.githubusercontent.com/argotorg/fe/v26.5.0/feup/feup.sh -o /tmp/feup.sh
# Review the installer before running it.
bash /tmp/feup.sh --version v26.5.0 --no-modify-path
export PATH="$HOME/.fe/bin:$PATH"
fe --version
fe build cli --backend native --emit executable
./cli/out/fairgrant_cli 10 6 3 3 4 1 10
```

Arguments are `BUDGET WEIGHT CAP [WEIGHT CAP ...]`. Amounts are unsigned atomic
units, not floating-point currency values. Output amounts are decimal **strings**
so JavaScript consumers cannot silently round a 128-bit amount.

```json
{"awards":["3","4","3"],"unallocated":"0","capped":[true,true,false],"rounded_up":[false,false,false]}
```

The first recipient's proportional share would exceed 3, and the second's
recomputed share would exceed 4. Those caps bind; the third receives the remaining
3. `capped` means the positive-weight, positive-cap recipient was removed at the
water-filling stage (including exact equality). `rounded_up` means the recipient
received one unit above its final proportional floor. These are distinct reasons.
A zero-cap recipient has both flags false.

## Real workflow: review a community grant budget

After building the Fe CLI above, run:

```sh
python3 scripts/report.py examples/community-grants.csv --budget 1000 --delta 100 --out review-community
python3 scripts/report.py examples/budget-risk.csv --budget 25 --delta 1 --out review-risk
# Open review-community/index.html and review-risk/index.html in your browser.
```

The first fictional committee caps Documentation at 300 and Translation at 400;
Fe redistributes the 1,000-unit budget into **300 / 400 / 300**. The second
shows a concrete policy trap: raising budget 25 to 26 reduces Teams D and E from
3 to 2. A reviewer sees that warning before approving a distribution.

Provide a UTF-8 CSV with header `name,weight,cap`, 1..16 unique recipient labels,
nonnegative integer weights (u64) and caps (u128). Input order is preserved and
is the tie-break rule. `--delta` compares three budgets (clamped to u128 limits),
not every intermediate budget. It cannot certify monotonicity.

A checked-in [example report](docs/demo.html) uses only fictional teams; download
and open it locally for a no-toolchain preview. Regenerate it with the risk
command above.

Each local review includes:
- `index.html`: readable, responsive result table, per-recipient reason, sensitivity
  warnings and a decision checklist; no JavaScript or external network requests.
- `allocation.csv`: exportable results with spreadsheet-formula-safe labels.
  Import amount columns **as text** in spreadsheets: automatic numeric import may
  round values longer than 15 digits. HTML and audit.json keep exact amounts.
- `audit.json`: selected budget/result and SHA-256 of the exact input CSV, so the
  reviewer can identify which policy input produced this decision.

The Python adapter only validates CSV, invokes the **actual compiled Fe executable**
for each scenario and renders its output. It does not reimplement allocation.
Existing output directories are refused to preserve prior review evidence.
Names are escaped in HTML; keep real participant CSVs/reports private. The
included examples are fictional. There is no hosted service or payment integration.

## Why another allocation library?

Simple `budget * weight / totalWeight` drops units and does not handle caps.
Capping the result afterward leaves money unused even when another eligible
recipient can accept it. FairGrant redistributes before integer rounding and
returns any genuinely unallocatable amount explicitly.

Examples:

| Budget | Weights | Caps | Awards | Unallocated |
|---|---|---|---|---|
| 10 | 1, 1, 1 | 10, 10, 10 | 4, 3, 3 | 0 |
| 10 | 1, 2, 3 | 10, 2, 10 | 2, 2, 6 | 0 |
| 100 | 1, 0, 2 | 3, 100, 4 | 3, 0, 4 | 93 |

## Fe-specific design

- The core has **no effects**: no `Ctx`, `Call`, storage or I/O. Its input fully
  determines its output. Host argument parsing and stdout are isolated in `cli/`.
- Fe's explicit numeric conversions make the arithmetic boundary visible:
  `u128` budgets/caps and `u64` weights widen to `u256` before multiplication;
  result narrowing uses checked `downcast()`. No unchecked allocation arithmetic.
- Invalid shape is a typed `Result<AllocationError, Plan>`, not a silent truncation.
  The API requires `count` in 1..16 and zero-filled unused array suffixes.
- One library is exercised by both Sonatina/EVM and native Fe test backends,
  then linked into a native executable. Python provides an independent test oracle and local CSV/report I/O; all report allocations still execute Fe.

See [the algorithm and bounds](docs/ALGORITHM.md),
[verification](docs/VERIFICATION.md), and [human walkthrough](docs/WALKTHROUGH.zh-CN.md).

## Verify

```sh
fe fmt --check
fe fmt cli --check
fe test
fe test --backend native
fe build cli --backend native --emit executable
python3 scripts/verify.py
```

The deterministic Python harness tests the compiled **Fe binary**, not a Python
replacement. Its exact `Fraction` oracle solves sorted cap/weight breakpoints,
independently of the Fe sequential removal loop. Seeded fixtures are also checked
into `src/vectors.fe` for both Fe backends.

To regenerate fixtures: `python3 scripts/verify.py --generate-vectors && fe fmt`.
To run more native cases: `python3 scripts/verify.py --cases 10000`.

## API

```fe
use fairgrant::allocate

let result = allocate(budget: 10,
    weights: [1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
    caps: [10,10,10,0,0,0,0,0,0,0,0,0,0,0,0,0], count: 3)
match result {
    Result::Ok(plan) => { /* plan.awards and plan.unallocated */ },
    Result::Err(error) => { /* reject the input */ },
}
```

An importing ingot may use `[dependencies] fairgrant = "../fairgrant"`.
Fixed capacity is intentional: at most 16 cap removals and 15 dust awards,
with no unbounded storage or allocation. Do not split a larger group into chunks:
that changes the mathematical allocation.

## Limits you should understand

- Largest-remainder (Hamilton) rounding is **not budget-monotone**. Raising the
  budget can lower a recipient's award. This is unsuitable for cumulative vested
  entitlements or incremental claim ledgers without a different policy.
- Equal remainders prefer the lower input index. Commit a canonical recipient
  order and all inputs before calculation. This library cannot enforce that.
- It cannot authenticate weights, prevent duplicate identities/Sybil attacks,
  decide eligibility, generate randomness, or make an allocation socially fair.
- At most 16 recipients; zero-weight recipients receive zero even with unused budget.
- Prototype, not externally audited; no production payment integration is claimed.
- The CLI accepts decimal integers only; malformed inputs return exit code 2.

## Contest and attribution

Prepared for the [Fe Builders Challenge](https://fe-lang.org/contest/) during its
November 3–24, 2026 build window. Human participant: **RiverSteel (Riversteel6)**.

**AI assistance:** OpenAI assistant agents proposed the scope, implemented code,
wrote tests and documentation, and performed automated review. RiverSteel is the
responsible human contact. This disclosure does not imply the human has already
reviewed or can explain every implementation detail; the included walkthrough is
for that review before final submission.

**Pre-existing work:** The starting repository was
[`fe-lang/builders-challenge-starter`](https://github.com/fe-lang/builders-challenge-starter)
at `f9d9aa92a03af82c2bbb0dc2e0810244eb13e686`. Its vault implementation was removed.
The Apache-2.0 license, manifest shape and initial CI template were retained/adapted.
Fe standard-library APIs and official native examples informed the CLI boundary.
The allocation algorithm is capped proportional water-filling plus Hamilton's
largest-remainder method; neither algorithm is claimed as new.

License: Apache-2.0. No private accounts, credentials, wallet addresses or email
addresses belong in this repository.
