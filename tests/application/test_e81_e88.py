from smart_money.application.provider_adapters import (
    LiquidityPoolProviderAdapter, SolanaRPCObservationAdapter, TokenMetadataProviderAdapter,
    WalletActivityProviderAdapter, build_provider_conflict_evidence, normalize_provider_payload,
)

def test_provider_adapters_normalize_and_conflict() -> None:
    for adapter in (SolanaRPCObservationAdapter(), TokenMetadataProviderAdapter(),
                    LiquidityPoolProviderAdapter(), WalletActivityProviderAdapter()):
        payload = normalize_provider_payload(adapter, {"slot": 10, "value": "x"})
        assert payload.metadata["classification"] == "EVIDENCE"
    conflict = build_provider_conflict_evidence("token", ("rpc-a", "rpc-b"), "VALUE_MISMATCH")
    assert conflict.evidence_id
