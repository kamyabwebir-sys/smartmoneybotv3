import json
from copy import deepcopy
from pathlib import Path

import pytest

from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.adapters.persistence.wallet_route_fixture import PURCHASE_WALLET
from smart_money.application.exact_swap_attribution import (
    build_exact_swap_attribution,
    project_exact_attribution_activity,
)
from smart_money.application.exact_swap_intelligence_binding import (
    bind_exact_swaps_to_intelligence,
)
from smart_money.application.solana_wallet_activity_aggregation import (
    aggregate_solana_wallet_activity,
)
from smart_money.application.solana_wallet_token_activity_ledger import (
    ingest_solana_wallet_token_activity,
)

FIXTURE = Path("fixtures/solana/mainnet/s12-trending-buy-candidate.json")
MINT = "mMHUFPJma7sGuFxYteoHJkfzb5iW6oLxsvVnUYfSTNK"


def payload() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["result"]


def test_real_fixture_projects_exact_integer_attribution_into_intelligence(
    tmp_path: Path,
) -> None:
    raw = payload()
    before = deepcopy(raw)

    attribution = build_exact_swap_attribution(raw, PURCHASE_WALLET)
    activity = project_exact_attribution_activity(attribution)
    ledger = DurableJsonEvidenceLedger(tmp_path / "activity-ledger.json")
    receipt = ingest_solana_wallet_token_activity(activity, ledger)
    replay = ingest_solana_wallet_token_activity(activity, ledger)
    aggregate = aggregate_solana_wallet_activity(ledger, wallet=PURCHASE_WALLET)

    assert raw == before
    assert attribution.direction == "BUY"
    assert attribution.quote_amount_raw == 9439420
    assert attribution.asset_amount_raw == 305853508248
    assert attribution.asset_mint == MINT
    assert len(attribution.pools) == 2
    assert attribution.wash_trade_confidence_bps == 0
    assert not attribution.suppressed
    assert activity.token_delta == attribution.asset_amount_raw
    assert receipt.evidence_id == replay.evidence_id and replay.already_present
    assert aggregate.buy_count == 1 and aggregate.token_count == 1


@pytest.mark.parametrize("mutation", ["signer", "native", "owner", "pool"])
def test_incomplete_or_conflicting_attribution_fails_closed(mutation: str) -> None:
    raw = payload()
    if mutation == "signer":
        raw["transaction"]["message"]["accountKeys"][0]["signer"] = False
    elif mutation == "native":
        raw["meta"]["postBalances"][0] -= 1
    elif mutation == "owner":
        raw["meta"]["postTokenBalances"][0]["owner"] = "other"
    else:
        raw["meta"]["innerInstructions"][0]["instructions"][0]["accounts"][5] = "wrong"

    with pytest.raises(ValueError):
        build_exact_swap_attribution(raw, PURCHASE_WALLET)


def test_exact_attribution_binds_to_existing_intelligence_and_ranking(
    tmp_path: Path,
) -> None:
    attribution = build_exact_swap_attribution(payload(), PURCHASE_WALLET)
    ledger = DurableJsonEvidenceLedger(tmp_path / "intelligence-ledger.json")

    binding = bind_exact_swaps_to_intelligence(
        (attribution,),
        ledger,
        reference_slots={MINT: attribution.slot},
        relationship_count=2,
        cohort_count=1,
        token_lifecycle_ids={MINT: "token-lifecycle-1"},
    )

    assert binding.profile.buy_count == 1
    assert binding.fingerprint.buy_ratio_bps == 10000
    assert binding.early_entry.consistency_bps == 10000
    assert binding.candidate_evidence.feature.relationship_count == 2
    assert binding.candidate_evidence.feature.cohort_count == 1
    assert binding.token_lifecycle_ids == ("token-lifecycle-1",)
    assert binding.ranking.rows[0].wallet == PURCHASE_WALLET
