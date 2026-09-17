from smart_money.adapters.solana_signature_normalizer import (
    SolanaSignatureNormalizer,
)
from smart_money.application.solana_candidate_pipeline import (
    build_wallet_profile,
    dashboard_candidate_view,
)
from tests.adapters.test_solana_signature_normalizer import _buy_payload


def test_normalized_signature_flows_into_candidate_read_model() -> None:
    normalized = SolanaSignatureNormalizer.normalize(_buy_payload())
    profile = build_wallet_profile(
        normalized.raw.signer,
        (normalized.candidate_activity(),),
    )
    dashboard = dashboard_candidate_view((profile,))

    assert profile.activity_count == 1
    assert profile.buy_count == 1
    assert profile.sell_count == 0
    assert dashboard["read_only"] is True
    assert dashboard["items"][0]["wallet"] == normalized.raw.signer
