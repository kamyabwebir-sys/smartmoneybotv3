# Quality coverage and live dashboard — 2026-09-17

## Delivered

### Quality evaluation

- A deterministic evaluator accepts only `candidate_evaluation_dataset.v1`
  documents explicitly marked `split=evaluation`.
- Candidate predictions enter precision/recall only after both Safety and
  Funding gates pass. Exclusions are reported independently.
- The bundled held-out corpus covers Raydium AMM/CPMM, Jupiter, Orca,
  Pump launch, plain transfer and cyclic-route negatives.
- Current bundled result: 8 samples, 2 TP, 1 FP, 1 FN, precision 66.66%,
  recall 66.66%, one Safety exclusion and one Funding exclusion.
- These numbers prove the evaluation path and its gate semantics. The bundled
  labels are a small curated fixture, not sufficient evidence of production
  predictive quality. A time-separated, independently labelled mainnet dataset
  is still required before any release claim.

Run:

```powershell
.venv/Scripts/python.exe scripts/evaluate_candidate_quality.py `
  fixtures/quality/independent-evaluation-v1.json
```

### Live dashboard

- `/api/v1/live/overview` reads the latest hash-verified SQLite batch archive.
- `/api/v1/live/candidates/{candidate_id}` returns route, swap and purchase evidence.
- `/api/v1/live/quality` exposes the held-out evaluation report.
- `/api/v1/live/reviews` accepts only `ACCEPTED` or `REJECTED` reviews for a
  candidate present in the latest batch.
- `/dashboard/live` refreshes every 15 seconds after a token is entered and
  displays batch counts, data age/staleness, Safety/Funding status, evidence,
  quality metrics and human-review controls.
- Live endpoints fail closed when the dashboard token is not configured.
  The static HTML shell remains public but cannot retrieve data without it.
- Safety/Funding values absent from the current ranking are displayed as
  `UNKNOWN`; the UI does not turn missing evidence into a pass.

Configuration example for the current PowerShell process:

```powershell
$env:SMART_MONEY_DASHBOARD_TOKEN = "replace-with-a-long-random-value"
$env:SMART_MONEY_LIVE_CAPTURE_DIR = "artifacts/solana/live_session.capture"
$env:SMART_MONEY_LIVE_REVIEW_STORE = "artifacts/dashboard/live_reviews.json"
$env:SMART_MONEY_LIVE_STALE_SECONDS = "300"
.venv/Scripts/python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/dashboard/live`. Do not commit the token. Binding
to a public interface requires TLS/reverse-proxy access controls outside this slice.

The dashboard is live with respect to the latest batch persisted by the runner;
it is polling-based, not WebSocket streaming. If acquisition stops, freshness
turns stale rather than presenting old evidence as current.

## Verification

- Targeted tests: 44 passed.
- Full pytest: 1455 passed, one upstream Starlette/AnyIO deprecation warning.
- Scoped Ruff: PASS.
- Boundary checker: PASS (330 files).
- Contract integrity: PASS.
- Protected Discovery registry and its test were not modified.
- Full compileall remains blocked by three pre-existing syntax-invalid modules:
  `src/smart_money/api/routes/dashboard.py`,
  `src/smart_money/api/routes/readiness.py`, and
  `src/smart_money/entrypoints/routes/wallet_intelligence.py`.

## Next production steps

1. Build a time-separated mainnet evaluation set with blinded/human-reviewed outcomes.
2. Project real Token Safety and Funding Graph evidence into every live ranking row.
3. Add review rationale, reviewer identity from authentication, and immutable review audit storage.
4. Run the batch collector continuously under a supervisor and test provider outage/reorg recovery.
5. Add pagination/query budgets and retention for growing batch archives.
6. Perform load tests, false-positive review and shadow operation before a human-gated release.
