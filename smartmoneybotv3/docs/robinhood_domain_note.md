# Robinhood Domain Note

Status: Provisional

## Current User Definition

Robinhood is a new Ethereum-based network/domain.

## Current Project Treatment

Robinhood is included as a priority target domain after Solana and alongside the future multi-domain architecture.

It remains provisional until technical validation is complete.

## Provisional Assumptions

Possible assumptions:
- Ethereum-based.
- Possibly EVM-compatible.
- May support token contracts.
- May need RPC/explorer/indexer access.
- May require a dedicated adapter.

These assumptions must not be treated as confirmed until validated.

## Required Validation

Before implementing a production adapter, confirm:
- Official technical documentation.
- Chain ID.
- RPC endpoints.
- Explorer availability.
- Token standards.
- Event/log semantics.
- Rate limits.
- Provider reliability.
- Data availability for wallet/token discovery.

## Adapter Rule

Do not hard-code Robinhood behavior into core contracts.

Implement Robinhood support through:
- adapters.
- chain/domain metadata.
- canonical mapping.
- fixtures.
- validation tests.

## Risk

If Robinhood semantics differ from standard EVM chains, chain-specific mapping must stay isolated in the adapter layer.
