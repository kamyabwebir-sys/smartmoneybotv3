from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload


def decode_pre_post_token_balances(pre: Mapping[str, int], post: Mapping[str, int]) -> tuple[dict[str, Any], ...]:
    keys = sorted(set(pre) | set(post))
    return tuple({"owner": key, "pre": int(pre.get(key, 0)), "post": int(post.get(key, 0)),
                  "delta": int(post.get(key, 0)) - int(pre.get(key, 0))} for key in keys)


def infer_buy_sell(delta: int) -> str:
    if not isinstance(delta, int) or isinstance(delta, bool):
        raise TypeError("delta must be integer")
    return "BUY" if delta > 0 else "SELL" if delta < 0 else "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PoolRoute:
    pool_id: str
    route: tuple[str, ...]
    route_id: str


def extract_pool_route(pool_id: str, route: tuple[str, ...]) -> PoolRoute:
    if not pool_id.strip() or not route or not all(isinstance(x, str) and x.strip() for x in route):
        raise ValueError("invalid pool route")
    identity = {"pool_id": pool_id.strip(), "route": route, "schema_version": "pool_route.v1"}
    return PoolRoute(pool_id, route, deterministic_id("pool_route", identity))


@dataclass(frozen=True, slots=True)
class ActivityEvidenceEnrichment:
    wallet: str
    token: str
    direction: str
    pool_id: str
    evidence_id: str


def enrich_activity(wallet: str, token: str, direction: str, pool_id: str) -> ActivityEvidenceEnrichment:
    if not wallet.strip() or not token.strip() or direction not in {"BUY", "SELL", "UNKNOWN"}:
        raise ValueError("invalid activity enrichment")
    identity = {"direction": direction, "pool_id": pool_id.strip(), "schema_version": "activity_enrichment.v1",
                "token": token.strip(), "wallet": wallet.strip()}
    return ActivityEvidenceEnrichment(wallet, token, direction, pool_id,
                                      deterministic_id("activity_enrichment", identity))


def detect_wash_or_self_route(wallet: str, route: tuple[str, ...]) -> tuple[bool, str]:
    if not wallet.strip() or not route:
        raise ValueError("wallet and route required")
    self_route = wallet in route
    return self_route, "SELF_ROUTE" if self_route else "NONE"


def detect_early_entry(entry_slot: int, first_observed_slot: int, window: int = 100) -> bool:
    if min(entry_slot, first_observed_slot, window) < 0:
        raise ValueError("slots and window must be non-negative")
    return entry_slot <= first_observed_slot + window


@dataclass(frozen=True, slots=True)
class ActivityCandidateRank:
    wallet: str
    token: str
    score: int
    rank: int


def rank_activity_candidates(candidates: tuple[Mapping[str, Any], ...]) -> tuple[ActivityCandidateRank, ...]:
    ordered = sorted(candidates, key=lambda x: (-int(x.get("score", 0)), str(x.get("wallet")), str(x.get("token"))))
    return tuple(ActivityCandidateRank(str(x["wallet"]), str(x["token"]), int(x.get("score", 0)), i)
                 for i, x in enumerate(ordered, 1))


def query_activity(candidates: tuple[Mapping[str, Any], ...], *, wallet: str | None = None,
                   token: str | None = None) -> tuple[Mapping[str, Any], ...]:
    return tuple(x for x in candidates if (wallet is None or x.get("wallet") == wallet.strip())
                 and (token is None or x.get("token") == token.strip()))


def project_activity_evidence(enrichment: ActivityEvidenceEnrichment, slot: int) -> EvidencePayload:
    return EvidencePayload(source_id="solana-activity", evidence_type="enriched_activity",
                           timestamp=slot, data={"activity": {"wallet": enrichment.wallet, "token": enrichment.token, "direction": enrichment.direction, "pool_id": enrichment.pool_id, "evidence_id": enrichment.evidence_id}},
                           metadata={"authority": "EXTERNAL_NON_AUTHORITATIVE", "classification": "EVIDENCE",
                                     "verification_status": "UNKNOWN",
                                     "provenance": {"evidence_id": enrichment.evidence_id}})


def verify_activity_replay(payload: EvidencePayload, replayed: EvidencePayload) -> bool:
    return payload.get_canonical_id() == replayed.get_canonical_id()


@dataclass(frozen=True, slots=True)
class ProductionDiscoveryReadinessGate:
    required_checks: tuple[str, ...]
    passed_checks: tuple[str, ...]
    ready: bool
    gate_id: str

    def __post_init__(self) -> None:
        expected = deterministic_id("production_discovery_readiness", {
            "passed_checks": self.passed_checks, "ready": self.ready,
            "required_checks": self.required_checks})
        if self.gate_id != expected:
            raise ValueError("gate_id mismatch")


def build_readiness_gate(required_checks: tuple[str, ...], passed_checks: tuple[str, ...]) -> ProductionDiscoveryReadinessGate:
    ready = bool(required_checks) and set(required_checks).issubset(passed_checks)
    identity = {"passed_checks": passed_checks, "ready": ready, "required_checks": required_checks}
    return ProductionDiscoveryReadinessGate(required_checks, passed_checks, ready,
                                            deterministic_id("production_discovery_readiness", identity))


__all__ = ["decode_pre_post_token_balances", "infer_buy_sell", "PoolRoute", "extract_pool_route",
           "ActivityEvidenceEnrichment", "enrich_activity", "detect_wash_or_self_route",
           "detect_early_entry", "ActivityCandidateRank", "rank_activity_candidates",
           "query_activity", "project_activity_evidence", "verify_activity_replay",
           "ProductionDiscoveryReadinessGate", "build_readiness_gate"]
