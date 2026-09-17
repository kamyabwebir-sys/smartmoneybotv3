# S12.1 — Owner balance reconciliation

Status: implemented and targeted-tested; repository release gate NOT passed.

Scope: pure Application projection, using the existing token delta extractor after
strict input validation. No RPC, file access, trading, ranking or public API changes.
Protected Discovery files were not edited.

Evidence contains per-mint raw integer deltas, decimals, signature, wallet, native
delta and the fee paid by this wallet. Zero deltas are retained. Multiple accounts
of one mint are aggregated. Missing owners, duplicate indices, changed identities,
decimal conflicts, failed transactions and incomplete balance arrays are rejected.
The evidence ID is independent of token balance row ordering.

Fee-adjusted native movement still includes rent and transfers; it is NOT swap
spend. Positive token movement does not establish BUY, arbitrage or dollar profit.
The input must contain resolved account keys; unresolved versioned keys are rejected
when their count does not match the native balance arrays. This projection does not
cryptographically verify signatures or certify provider completeness.

Verification:
- Targeted pytest: 15 passed.
- Ruff (two added Python files): PASS.
- Boundary enforcer: PASS (324 files).
- Contract integrity: PASS.
- Full pytest: 1353 passed, 1 failed, 1 warning.
- Failure: test_session_recovery_store_rejects_overwrite_and_corruption expects
  `rollback`, but receives `DashboardSessionRecoveryReceipt identity collision`.
  The failing persistence module already had working-tree changes and was not
  edited in this slice. No claim of a clean baseline is made.

Next bounded steps (not implemented):
1. S12.2: persist the real transaction fixture and reproduce this projection.
2. S12.3: resolve parsed transfers and instruction routes, retaining unknowns.
3. S12.4: classify intermediate/round-trip evidence separately from directional
   accumulation; require evidence beyond balance signs.
4. S12.5: wire the verified classification into candidate ranking and dashboard,
   with regressions for fee-only native changes and intermediate tokens.

No release, commit, mainnet fixture verification or ranking integration completed.
