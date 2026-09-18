from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_program_decoders import program_kind
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload


def fetch_transaction_batch(fetcher: Callable[[str], Mapping[str, Any]],
                            signatures: tuple[str, ...]) -> tuple[Mapping[str, Any], ...]:
    if not callable(fetcher) or not isinstance(signatures, tuple):
        raise TypeError("invalid fetcher or signatures")
    return tuple(fetcher(signature) for signature in signatures)


def extract_rpc_balances(response: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    if not isinstance(response, Mapping):
        raise TypeError("response must be mapping")
    result = response.get("result", response)
    if not isinstance(result, Mapping):
        raise ValueError("RPC result must be mapping")
    return tuple({"owner": owner, "pre": int(value.get("pre", 0)), "post": int(value.get("post", 0)),
                  "delta": int(value.get("post", 0)) - int(value.get("pre", 0))}
                 for owner, value in sorted(result.get("balances", {}).items()))


def classify_program_swap(program_id: str, instruction: Mapping[str, Any]) -> str:
    kind = program_kind(program_id)
    if instruction.get("type") not in {"SWAP", "ROUTE"}:
        return "UNKNOWN"
    return f"{kind}_SWAP"


@dataclass(frozen=True, slots=True)
class ResolvedPoolRoute:
    pool_id: str
    route: tuple[str, ...]
    resolution_id: str


def resolve_pool_route(pool_id: str, route: tuple[str, ...]) -> ResolvedPoolRoute:
    if not pool_id.strip() or not route:
        raise ValueError("pool and route are required")
    identity = {"pool_id": pool_id.strip(), "route": route, "schema_version": "resolved_pool_route.v1"}
    return ResolvedPoolRoute(pool_id, route, deterministic_id("resolved_pool_route", identity))


def project_wallet_activity(ledger: EvidenceLedger, wallet: str, token: str, slot: int, delta: int) -> str:
    payload = EvidencePayload(source_id="production-discovery", evidence_type="wallet_activity_evidence",
                              timestamp=slot, data={"wallet": wallet, "token": token, "delta": delta},
                              metadata={"authority": "EXTERNAL_NON_AUTHORITATIVE", "classification": "EVIDENCE",
                                        "verification_status": "UNKNOWN"})
    identity = payload.get_canonical_id()
    if ledger.append(payload) != identity:
        raise ValueError("ledger identity mismatch")
    return identity


def project_token_activity(ledger: EvidenceLedger, token: str, wallet: str, slot: int, delta: int) -> str:
    return project_wallet_activity(ledger, wallet, token, slot, delta)


def project_early_entry(wallet: str, token: str, entry_slot: int, first_slot: int) -> EvidencePayload:
    early = entry_slot <= first_slot
    return EvidencePayload(source_id="production-discovery", evidence_type="early_entry_evidence",
                           timestamp=entry_slot, data={"wallet": wallet, "token": token, "early": early},
                           metadata={"authority": "NONE", "classification": "EVIDENCE",
                                     "verification_status": "UNKNOWN"})


def project_wash_trade(wallet: str, route: tuple[str, ...]) -> EvidencePayload:
    detected = wallet in route
    return EvidencePayload(source_id="production-discovery", evidence_type="wash_trade_evidence",
                           timestamp=0, data={"wallet": wallet, "route": list(route), "detected": detected},
                           metadata={"authority": "NONE", "classification": "EVIDENCE",
                                     "verification_status": "UNKNOWN"})


def rank_production_candidates(candidates: tuple[Mapping[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    ordered = sorted(candidates, key=lambda item: (-int(item.get("score", 0)), str(item.get("wallet", ""))))
    return tuple({**dict(item), "rank": index} for index, item in enumerate(ordered, 1))


def verify_production_discovery_gate(required: tuple[str, ...], passed: tuple[str, ...]) -> bool:
    return bool(required) and set(required).issubset(passed)


__all__ = ["fetch_transaction_batch", "extract_rpc_balances", "classify_program_swap",
           "ResolvedPoolRoute", "resolve_pool_route", "project_wallet_activity",
           "project_token_activity", "project_early_entry", "project_wash_trade",
           "rank_production_candidates", "verify_production_discovery_gate"]
