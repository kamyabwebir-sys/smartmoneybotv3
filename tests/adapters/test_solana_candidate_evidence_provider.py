from smart_money.adapters.solana_candidate_evidence_provider import (
    SolanaCandidateEvidenceProvider,
)


def test_provider_projects_authority_holders_pool_and_price() -> None:
    def rpc(method, _params):
        if method == "getAccountInfo":
            return {"result": {"value": {"data": {"parsed": {"info": {"mintAuthority": None, "freezeAuthority": None}}}}}}
        return {"result": {"value": [{"amount": "20"}, {"amount": "10"}]}}

    provider = SolanaCandidateEvidenceProvider(rpc)
    assert provider.authority("mint", observed_slot=7).mint_authority is None
    assert provider.holder_distribution("mint", observed_slot=7, supply_raw=100).top_holders_bps == 3000
    assert provider.pool_reserves(mint="mint", pool="pool", quote_mint="USDC", base_reserve_raw=10, quote_reserve_raw=20, observed_slot=7).quote_reserve_raw == 20
    assert provider.point_in_time_price(mint="mint", quote_mint="USDC", observed_at=9, slot=7, asset_amount_raw=10, quote_value_raw=20).quote_value_raw == 20
