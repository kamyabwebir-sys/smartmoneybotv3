# S12.2–S12.5: bounded fixture-to-dashboard implementation

## Delivered

- S12.2: real configured-RPC response saved as `fixtures/solana/mainnet/s12-cycle.json`.
  Offline loader pins SHA256, transaction signature and deterministic projection ID.
  Hash pinning detects local drift; it is not independent proof of chain consensus.
- S12.3: ordered top-level/inner instruction inventory, 9 resolved SPL token
  transfer edges, explicit endpoint ownership/mint/decimals, transfer/balance checks.
  Unknown endpoints or unsupported token operations block classification.
- S12.4: INTERMEDIATE, ROUND_TRIP_FLOW, NET_INFLOW, NET_OUTFLOW, UNCHANGED, UNKNOWN.
  ROUND_TRIP_FLOW means both incoming and outgoing owner flow, NOT a proven
  cyclic DEX route. NET_INFLOW means accumulation of balance, NOT a verified BUY.
- S12.5: exclusion option on existing candidate ranker, used by the new evidence
  read path. `/api/v1/route-evidence` replays the pinned fixture offline.
  `/dashboard/route-evidence` displays Persian classifications, raw units/decimals,
  eligibility, transfer edges and program invocation inventory.

## Important limits

Exact pool mapping, full swap instruction decoding, proven arbitrage, dollar profit,
cross-transaction wallet ranking and live batch integration remain unimplemented.
No evidence here establishes a verified directional purchase: eligibility remains
false, scores zero. Existing legacy callers retain their previous behavior unless
they supply exclusions; this is NOT a global fix to legacy ranking.
Token-2022 fees and unsupported balance-changing operations can produce gaps and
must not be silently accepted. No pool is guessed from an arbitrary account.

The API uses existing historical read authorization. Existing deployment permits
anonymous reads when no token is configured; production authentication was NOT
enabled by this slice. HTML shell contains no embedded fixture or token. Browser
rendering has not been manually verified; TestClient checks API and HTML serving.

## File scope

- Added fixture: `fixtures/solana/mainnet/s12-cycle.json`
- Added projection: `src/smart_money/application/wallet_route_evidence.py`
- Added offline adapter: `src/smart_money/adapters/persistence/wallet_route_fixture.py`
- Updated ranker: `src/smart_money/application/solana_candidate_pipeline.py`
- Added router: `api/routes/route_evidence.py`
- Updated router registration: `api/main.py`
- Added UI: `api/static/route-evidence.html`
- Added tests: `tests/application/test_wallet_route_evidence.py`
- Added this note. Protected Discovery files untouched; unrelated edits preserved.

## Verification

Ruff on all changed Python files: PASS. Boundary: PASS (325 files).
Contract integrity: PASS. Full-suite result is reported in the handoff.
Known unrelated failure: recovery store test expects `rollback`, receives
`DashboardSessionRecoveryReceipt identity collision`; no baseline release claimed.

Next: verify actual pool/instruction semantics using program-specific fixtures;
then apply evidence exclusions to the live batch consumer with an end-to-end test.
Do not declare a full S12 production gate from this one-transaction inspection.
