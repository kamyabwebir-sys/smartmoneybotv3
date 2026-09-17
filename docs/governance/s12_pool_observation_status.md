# S12 pool state observation — partial task completion

Delivered: finalized getMultipleAccounts response for the two existing pools,
slot 447647895. Transaction slot is 447616755. Owner, non-executable account,
binary layout, mint pair and paired vault mappings match the two decoded swap
instructions. Snapshot hash is pinned by the offline loader and observations
are exposed in the existing dashboard swap section. Historical-state verification
is explicitly false, even for a same-slot response (no intra-slot proof).

Primary layout references consulted:
- raydium-io/raydium-cp-swap: programs/cp-swap/src/states/pool.rs
- raydium-io/raydium-sdk-V2: src/raydium/liquidity/layout.ts
- Solana RPC getMultipleAccounts documentation.

New files: application/pool_state_observation.py,
tests/application/test_pool_state_observation.py,
scripts/capture_directional_sample.py, fixtures/solana/mainnet/s12-pool-observation.json,
and raw investigation responses under fixtures/solana/mainnet/s12-search/.
Updated verified_swap_legs.py to retain vault references and wallet_route_fixture.py
to bind current pool observations. Protected Discovery files untouched.

NOT delivered: a positively verified real directional-buy fixture. Local fixture
search found no matching single-leg sample. Bounded RPC searches over the two pools
and CPMM program also found none (last run examined 49 distinct signatures; some
were unavailable from RPC). Saved investigation fixtures are not positive examples.
They include intermediate/round-trip flows, unsupported operations, and unresolved
accounts. Do not loosen acceptance or claim recall validation from this corpus.

The capture script stops on an eligible sample or after at most 60 signature rows
per run, never trades, and preserves the primary fixture paths when present.
Its candidate filter is preliminary, NOT a BUY verdict. No positive ranking policy
was enabled; existing exclusions and closed production gate remain unchanged.

Next: obtain a supported single-leg directional BUY with complete account ownership
(ideally pre-existing quote token account), capture it with signature/slot provenance,
then implement and adversarially test positive acceptance. Native SOL wrapping/rent
and unrecognized instructions require explicit decoders, not missing-data defaults.
