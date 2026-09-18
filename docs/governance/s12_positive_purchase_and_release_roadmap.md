# S12 positive purchase and remaining release roadmap

## Verified scope of this change

Real fixture: `fixtures/solana/mainnet/s12-trending-buy-candidate.json`.
Raw-file SHA256: de43f8e327b8bdaa70b9cc69cb25c096b3e50abc6e01f0138d643145aba48782.
Purchase ID: observed_directional_purchase_a606d87b7e0c5157266f13770a5ac247.

- Decode Raydium CLMM swap_v2 exact-input (41-byte layout, input flag true,
  pool index 2, user accounts 3/4, vaults 5/6, mints 11/12) plus CPMM input swap.
- Validate two direct token CPIs per leg and their amounts, account mappings and
  token-program binding. Token-2022 is accepted ONLY if all observed pre-existing
  accounts reconcile exactly to parsed transfers. Hooks, unexplained withheld fees,
  account creation/closure and unsupported operations remain excluded.
- Positive purchase requires one Jupiter outer invocation, a signing owner,
  an acyclic connected chain of supported legs, USDC funding, final net token
  inflow, zero intermediate net balances and no unexplained asset movement.
- Separate 47434 raw USDC auxiliary outflow is disclosed, not given a guessed fee
  type. USDC spent: 9486854 raw; LinkedInu received: 305853508248 raw.
- Rank exactly one output token, not the intermediate asset or quote currency.
  Rank scores are ordering weights, NOT calibrated probabilities or profitability.
- Batch runner uses this decision and persists it. Duplicate signatures fetch once.
  Existing production gate stays false; a positive purchase is not a release.
- Existing API accepts `sample=purchase` (or default `cycle`), with the existing
  read authorization. Dashboard selector shows both examples using one request.
- Negative-cycle fixture remains rejected. Original wallet_route_evidence.v1 and
  its pinned ID are unchanged; purchase assessment is a separate projection, not
  a Ledger schema migration or a new receipt chain.

## Source and trust boundaries

Consulted official sources:
- https://raw.githubusercontent.com/raydium-io/raydium-clmm/master/programs/amm/src/instructions/swap_v2.rs
- https://raw.githubusercontent.com/raydium-io/raydium-cp-swap/master/programs/cp-swap/src/instructions/swap_base_input.rs
- https://raw.githubusercontent.com/jup-ag/jupiter-cpi/main/idl.json

The public Jupiter CPI IDL consulted did not include route_v2. Therefore this
implementation does NOT claim full Jupiter instruction decoding. It assesses
observed economic purchase from successful RPC results, exact supported downstream
swap legs and reconciled balances. Historical pool account state, deployed program
bytecode and cryptographic transaction signatures are not independently verified.
Current pool snapshots from earlier work are not historical-state proof.
Do not relabel this as complete Token-2022 support or a smart-money finding.

## Verification and changed files

50 targeted tests passed. Includes positive and
negative real fixtures, 18 adversarial mutations, signature deduplication, actual
CLI with injected RPC through persisted output, API auth and hash-tamper rejection.
Ruff on modified Python files passes after import formatting. Contract integrity
passes. Full suite: 1428 passed, 10 failed, one deprecation warning. Failures:
the existing recovery-store rollback/message discrepancy and nine tests in
tests/discovery/test_consumer.py (ordering, required fields, score validation).
The Discovery consumer was not edited by this slice; its changes must be audited
before fixing or overwriting it. This worktree was not a stable clean baseline.

Boundary initially passed (328 files). Final checker found pre-existing/out-of-scope
Core files now containing UTF-8 BOM: core/errors.py and core/events.py. This slice
did not edit them. No boundary bypass, protected Discovery change or commit made.
Browser visual verification and a fresh live mainnet run of the changed runner
were not performed; tests use captured real RPC data through an injected transport.

Added:
- src/smart_money/application/directional_purchase.py
- tests/application/test_directional_purchase.py
- this document

Updated:
- src/smart_money/application/verified_swap_legs.py
- src/smart_money/application/live_route_batch.py
- src/smart_money/adapters/persistence/wallet_route_fixture.py
- api/routes/route_evidence.py
- api/static/route-evidence.html

## Final roadmap: outcomes, not endless slice numbering

This roadmap reflects verified S12 work plus remaining release requirements. Earlier
phase names in chat are not evidence that every historical implementation is complete.
No completion percentage is assigned.

```text
SmartMoney Intelligence (read-only; no trade execution)
├── Existing foundations — contract/evidence/replay/identity/storage infrastructure
│   └── Re-audit actual wiring; do not rewrite every store or add receipt layers
├── S12 transaction evidence — IN PROGRESS, positive & negative fixture coverage
│   ├── Owner balances, observed transfers, two supported Raydium layouts + CLMM
│   ├── Positive purchase / excluded intermediate assets / batch & API integration
│   └── Remaining: broader corpus, Jupiter semantics, native SOL rent/wrapping,
│       Token-2022 extension limits, frozen official layout/version references
├── Release milestone A — reproducible clean baseline
│   ├── Resolve BOM boundary regressions without overwriting unrelated work
│   ├── Resolve rollback vs identity-collision persistence contract discrepancy
│   ├── Audit current Discovery consumer changes and its nine failing tests
│   └── Exit: full tests + boundaries + contracts + scoped lint green; reviewed commit
├── Release milestone B — operational acquisition and dataset
│   ├── One actual runner, bounded RPC budgets/rate limits and retries
│   ├── Durable raw-fixture capture, deduplication and checkpoint recovery
│   ├── Backfill -> hot/cold archive -> reproducible replay on real samples
│   └── Exit: crash/restart resumes without data loss/double counts; missing data visible
├── Release milestone C — intelligence quality
│   ├── Token safety provenance/freshness and funding relationships joined to candidates
│   ├── Early-entry/profile metrics, explicit unknowns, service/router exclusions
│   ├── Held-out outcomes, leakage checks, precision/recall and calibration
│   └── Exit: independently labelled real evaluation set and declared error bounds;
│       one purchase does not certify a wallet's smart-money skill
├── Release milestone D — live usable dashboard and alerts
│   ├── Live batch read-model refresh (not only pinned example fixtures)
│   ├── Wallet/token detail, evidence drill-down, timestamps and rejection reasons
│   ├── Persistent human review, read auth, query budgets, safe rendering
│   └── Exit: browser E2E proves new observations appear; stale/error state visible;
│       no key exposure, no unauthorized writes, no automated trading
├── Release milestone E — measured shadow operation
│   ├── Time-bounded real RPC run, error/latency/freshness/CPU/RAM/storage metrics
│   ├── Disconnect, corruption, restart and load drills on target server
│   ├── RPC cost/quota caps, archive growth budgets and operator stop control
│   └── Exit: agreed SLOs met and representative candidates manually reviewed
└── Release milestone F — human-gated distribution
    ├── Frozen source/artifact/dependency inventory, reproducible install and rollback
    ├── Secret/dependency scan, restore test, runbook and known limitations
    └── Exit: signed-off operator review and demonstrably reversible release
```

Immediate next priority: A, then a small real acquisition + live-dashboard vertical
run from B/D. Do not wait for every protocol decoder to be perfect; clearly mark
unsupported routes and measure coverage. Run C and E on that collected dataset.
New receipt/persistence layers are justified only by an observed recovery/audit gap.
