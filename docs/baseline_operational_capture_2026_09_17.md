# Baseline and bounded operational capture — 2026-09-17

## Scope and status

Requested scope: restore the baseline contracts and add durable acquisition to
the existing `scripts/live_rpc_runner.py`. No trading, no new receipt hierarchy,
no changes to protected Discovery registry files. No commit or cleanup performed.

Baseline fixes:

- Removed BOM from `core/errors.py` and `core/events.py`; modernized their Mapping imports.
- Restored Discovery string/type, unique evidence-reference and canonical value validation.
- Kept the generic recovery-store refactor, restoring its original hashed v1
  envelope and immutable/rollback rejection. Other generic stores retain defaults.
- Unhashed receipts written by the incompatible refactor are rejected, not
  silently upgraded. Recover those from an independently verified source.

## One runner, bounded backfill

With `SOLANA_RPC_URL` securely configured and `SOLANA_NETWORK=mainnet-beta`:

```powershell
.venv/Scripts/python.exe scripts/live_rpc_runner.py `
  --wallet 2FRFWM24vDbdCfs7k6at3dqtNKDVHghdZ1d6zmw5w2S2 `
  --limit 20 --pages 2 `
  --state-dir artifacts/solana/capture-directional-example `
  --output artifacts/solana/directional-example.json
```

This address is an existing fixture subject, not a certified smart-money wallet.
The command consumes RPC quota. It was not executed against mainnet in this slice.
Repeat the same command and state directory to resume. A pending page requires
the same `--limit`. Default: one page, twenty signatures. Maximum per invocation:
100 pages, 1,000 rows/page. Use small limits initially.

Storage:

```text
state-dir/
├── runner.lock          OS-held single-writer lock; inert file may remain
├── capture.sqlite3     raw responses, hashes, page reports, processed keys, cursor
├── capture.sqlite3-wal SQLite-managed, while active
└── capture.sqlite3-shm SQLite-managed, while active
output.json             atomic export of the LAST page result, not all-page ranking
```

- SQLite WAL with synchronous FULL; raw responses commit before decoding.
- Pending signature page survives interruption. Cached transaction responses
  are not fetched again, and overlapping completed signatures are not reprocessed.
- Page report, processed markers and cursor commit in one transaction.
- Null/missing/wrong-signature transactions retain the pending page and cursor.
  Exit status 2 means page incomplete; 0 means page acquisition complete, **not**
  production approval. Decoder failures remain explicit in the page report.
- Raw responses are archived even when decoding rejects them. A decoder rejection
  does not cause endless acquisition of the same valid raw transaction.
- Hash corruption fails closed. Hashes detect accidental modification, not a
  malicious writer able to replace both content and hash.
- Wallet/network mismatch rejects reuse of the state directory. No RPC URL or key
  is written to this store by the runner.
- Transient HTTP/network failures: at most four attempts with default settings,
  exponential delay capped at ten seconds. Permanent HTTP and RPC error responses
  do not retry automatically. No nested runner retries. An operator rerun creates
  a new bounded attempt budget.
- The lock is released by the OS after termination; do not delete active SQLite
  WAL/SHM files. Back up a stopped store or use SQLite's backup API.

## Explicit limits

This is descending `before`-cursor historical acquisition, not continuous head
polling. An exhausted state remains exhausted. Future live polling needs separate
head-watermark and overlap/reorg semantics; do not reset this checkpoint to fake it.
Raw archive identity is checked against the requested signature, but this does not
cryptographically prove RPC truth. Finality/reorg reconciliation, archive retention,
provider pruning and real-world outage tests remain separate production work.
The dashboard has not been wired to this new archive in this slice.

## Verification

- Full pytest: **1451 passed**, one Starlette/AnyIO deprecation warning.
- Boundary checker: PASS (329 files); contract integrity: PASS.
- New tests cover process termination, pending-page resume, atomic checkpoint
  rollback, cross-page deduplication, single writer, hash corruption, wrong identity,
  absent transactions, bounded retry and redacted transport errors.
- Full-repository Ruff: **814 findings** outside a clean-release claim. Do not
  equate green pytest with a lint-clean or production-ready repository.
- Scoped Ruff: PASS on the files changed in this slice.

## Changed files in this slice

```text
src/smart_money/
├── core/errors.py
├── core/events.py
├── discovery/consumer.py
└── adapters/
    ├── solana_rpc_fetcher.py
    └── persistence/
        ├── generic_value_store.py
        ├── dashboard_session_recovery_receipt_store.py
        └── live_capture_store.py                     [new]
scripts/live_rpc_runner.py
tests/adapters/
├── test_solana_rpc_bounded_retry.py                  [new]
└── persistence/
    ├── test_dashboard_session_recovery_receipt_store.py
    └── test_live_capture_store.py                    [new]
docs/baseline_operational_capture_2026_09_17.md        [new]
```

## Remaining path

1. Classify and resolve repository-wide lint/syntax debt, without bulk-changing contracts.
2. Bounded mainnet acquisition smoke test and independent replay from archived raw data.
3. Finality-aware continuous head polling and real interruption/provider outage drill.
4. Connect accumulated verified candidates to dashboard; retain uncertainty and failures.
5. Real outcome labels, walk-forward quality evaluation and false-positive review.
6. Shadow operation with resource budgets, retention, recovery and human-gated release.
