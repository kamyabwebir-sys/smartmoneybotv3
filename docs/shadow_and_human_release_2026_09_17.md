# Real enrichment, shadow production and human release gate — 2026-09-17

## Candidate enrichment

Run the existing acquisition runner with real Solana RPC enrichment:

```powershell
.venv/Scripts/python.exe scripts/live_rpc_runner.py `
  --wallet <WALLET> --limit 20 --pages 1 --mode head `
  --enrich-safety-funding `
  --state-dir artifacts/solana/live-session `
  --output artifacts/solana/live-session.json
```

- Token Safety reads parsed mint state via `getAccountInfo` and holder
  concentration via `getTokenLargestAccounts`; raw provider responses are cached.
- Mint/freeze authority produces `RISK_PRESENT`. Missing or malformed evidence is
  `INCOMPLETE`, never a pass. A complete observation with no authority is
  `EVIDENCE_COMPLETE`; this is evidence status, not a buy recommendation.
- Funding edges are only parsed incoming native System Program transfers observed
  in captured transactions. Missing edges are `NOT_OBSERVED`, not proof of no link.
- Enrichment does not alter the deterministic candidate score. Provenance and
  evidence are attached to each row for review and replay.

## Mainnet evaluation dataset

`scripts/build_mainnet_evaluation_dataset.py` joins pre-outcome discoveries with
later human outcome labels. It rejects training-set overlap, wrong-chain rows,
duplicate identities and labels not strictly later than discovery. No production
dataset was fabricated in this slice: real future outcome labels are still needed.

## Continuous shadow operation

```powershell
.venv/Scripts/python.exe scripts/shadow_production_runner.py `
  --wallet <WALLET> `
  --state-dir artifacts/solana/shadow-live `
  --output artifacts/solana/shadow-live.json `
  --metrics artifacts/operations/shadow-live.jsonl `
  --limit 20 --cycles 0 --interval-seconds 30 --max-rss-mb 512
```

`cycles=0` runs until interrupted. Each child session is isolated, uses head-mode,
resumes the durable archive, and appends an fsync'd metric containing elapsed time,
peak RSS, archive bytes, exit status, RPC request/retry counts, page completion and
optional RPC cost. Monetary cost remains null unless
`SOLANA_RPC_COST_PER_MILLION_USD` is explicitly configured.

The September 17, 2026 bounded smoke used one cycle and one signature:

```text
exit=0, elapsed=1047ms, peak_rss=5,185,536 bytes
archive=131,072 bytes, rpc_requests=1, retries=0, page_complete=true
```

The first smoke also exercised real Safety enrichment. Funding was not observed in
that small sample and remained `NOT_OBSERVED`. This is not a long-duration load test.

## Human release gate

The release gate requires all of the following:

1. clean committed worktree;
2. successful reproducible offline packaging report;
3. source and rollback bundle hash match;
4. secret scan of `src`, `api`, `scripts` and the rollback ZIP;
5. SQLite backup plus restore drill with exact record comparison;
6. explicit operator identity and phrase `I_APPROVE_READ_ONLY_RELEASE`.

```powershell
.venv/Scripts/python.exe scripts/operator_release_gate.py `
  --capture-db artifacts/solana/shadow-live/capture.sqlite3 `
  --packaging-report artifacts/release/packaging-report.json `
  --release-dir artifacts/release/human-gate `
  --operator <OPERATOR-ID> `
  --approval I_APPROVE_READ_ONLY_RELEASE
```

The authority in the receipt is limited to read-only shadow release. It does not
authorize trading. Current release status is **BLOCKED** because the worktree is not
clean/committed and the packaging artifacts predate these changes.

## Security note

A credential-bearing RPC URL was found in `scripts/get_real_sig.py` and replaced
with environment-based configuration. The working-tree and existing rollback ZIP
now scan with zero findings under this gate's patterns. The exposed provider key
must still be revoked/rotated because deletion from the current file does not erase
prior copies, logs, backups or Git history.
