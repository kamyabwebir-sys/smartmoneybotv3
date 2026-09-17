# S12 live batch swap binding

No new receipt chain. The live runner now fetches one signature page and each
distinct transaction once, projects strict owner-flow evidence and applies the
existing ranking exclusion path. Null/failed/mismatched-signature RPC results
remain failures, not empty successful observations. The CLI session schema is now
`route_checked_live_batch.v1`; consumers of the old audit/replay summary must not
assume those fields remain. Older helper functions were not globally migrated.

## Decoder scope and primary references

- https://raw.githubusercontent.com/raydium-io/raydium-cp-swap/master/programs/cp-swap/src/instructions/swap_base_input.rs
- https://raw.githubusercontent.com/raydium-io/raydium-amm/master/program/src/instruction.rs

Read official sources during implementation. These URLs are moving branches, not
pinned deployment attestations. CPMM base input uses the Anchor discriminator,
13 accounts and pool index 3. AMM base-in-v2 uses tag 16, 8 accounts and pool
index 1. Check exact input amount, minimum output, direct descendant transfer
scope, source/destination, vault accounts and mint pair. Unsupported layouts and
Token-2022 fee semantics do not verify. No arbitrary first-account pool heuristic.

Real fixture legs:
1. Pool 4MXybVn82rBxjvANiMpmvYUQejRzwkiTnjDT8NQmHMRe:
   80000000000 raw lola -> 185305375 raw WSOL.
2. Pool 3RZcRvdU4osDJKDmhCyKqhU5eF8F8Lsy9BDghAM8RmvA:
   185305375 raw WSOL -> 235068942933 raw STORE.

`INSTRUCTION_AND_TRANSFERS_MATCH` means structural evidence from the supplied
successful RPC response. It does not prove historical pool account state, deployed
bytecode, complete Jupiter/custom-program intent, sandwiching or profitability.
Full route remains unverified; the unrelated custom outer program is not decoded.
Both observed tokens remain excluded from directional BUY ranking. In fact all
transfer-only results remain ineligible until directional intent is implemented;
the gate is deliberately false, not a production approval.

## Verification and files

19 targeted tests passed (includes actual runner CLI through injected RPC,
persisted output, no double fetch, deterministic fixture replay and malicious
amount/vault/data/height/program edits). This is offline end-to-end testing, not
a fresh live mainnet batch or browser visual test.
Ruff PASS; Boundary PASS (327 files); full suite result in handoff.

Added application/verified_swap_legs.py, application/live_route_batch.py and
tests/application/test_live_route_batch.py. Updated scripts/live_rpc_runner.py,
adapters/persistence/wallet_route_fixture.py and api/static/route-evidence.html.
This document is the only new governance file. Protected Discovery untouched.

Next: pool account-state capture with slot provenance and custom/Jupiter route
intent decoding, plus a genuine directional-buy positive fixture. Do not relax
the exclusions merely to produce candidates. No additional receipt layers needed.
