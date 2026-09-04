from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class TokenSafetyProductionProfile:
    token: str
    summary_id: str
    total_rules: int
    triggered_rules: int
    safety_score_bps: int
    production_id: str
    schema_version: str = "token_safety_production_profile.v1"


def build_token_safety_production_profile(
    token: str,
    summary_id: str,
    total_rules: int,
    triggered_rules: int,
) -> TokenSafetyProductionProfile:
    if not isinstance(token, str) or not token.strip():
        raise ValueError("token must be non-empty")
    if not isinstance(summary_id, str) or not summary_id.strip():
        raise ValueError("summary_id must be non-empty")
    for value, name in ((total_rules, "total_rules"), (triggered_rules, "triggered_rules")):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be non-negative integer")
    if total_rules == 0 or triggered_rules > total_rules:
        raise ValueError("invalid rule counts")
    safety_score_bps = (total_rules - triggered_rules) * 10000 // total_rules
    identity = {
        "schema_version": "token_safety_production_profile.v1",
        "summary_id": summary_id.strip(),
        "safety_score_bps": safety_score_bps,
        "token": token.strip(),
        "total_rules": total_rules,
        "triggered_rules": triggered_rules,
    }
    return TokenSafetyProductionProfile(
        token.strip(), summary_id.strip(), total_rules, triggered_rules,
        safety_score_bps, deterministic_id("token-safety-production-profile", identity),
    )


@dataclass(frozen=True, slots=True)
class OpportunityRanking:
    subject_id: str
    wallet: str
    token: str
    wallet_score_bps: int
    token_safety_bps: int
    opportunity_score_bps: int
    rank: int
    ranking_id: str
    schema_version: str = "wallet_token_opportunity_ranking.v1"


def rank_wallet_token_opportunities(
    opportunities: tuple[Mapping[str, object], ...],
) -> tuple[OpportunityRanking, ...]:
    if not isinstance(opportunities, tuple) or not opportunities:
        raise ValueError("opportunities must be a non-empty tuple")
    rows: list[OpportunityRanking] = []
    for item in opportunities:
        if not isinstance(item, Mapping):
            raise TypeError("opportunities must contain mappings")
        try:
            subject_id = str(item["subject_id"]).strip()
            wallet = str(item["wallet"]).strip()
            token = str(item["token"]).strip()
            wallet_score = item["wallet_score_bps"]
            token_safety = item["token_safety_bps"]
        except KeyError as exc:
            raise ValueError(f"missing opportunity field: {exc}") from exc
        if not subject_id or not wallet or not token:
            raise ValueError("opportunity identity fields must be non-empty")
        if any(
            isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10000
            for value in (wallet_score, token_safety)
        ):
            raise ValueError("scores must be integer basis points")
        score = (wallet_score + token_safety) // 2
        rows.append(OpportunityRanking(
            subject_id, wallet, token, wallet_score, token_safety, score, 0, "",
        ))
    ordered = sorted(rows, key=lambda row: (-row.opportunity_score_bps, row.subject_id))
    result: list[OpportunityRanking] = []
    for index, row in enumerate(ordered, start=1):
        identity = {
            "opportunity_score_bps": row.opportunity_score_bps,
            "rank": index,
            "schema_version": "wallet_token_opportunity_ranking.v1",
            "subject_id": row.subject_id,
            "token": row.token,
            "wallet": row.wallet,
        }
        result.append(OpportunityRanking(
            row.subject_id, row.wallet, row.token, row.wallet_score_bps,
            row.token_safety_bps, row.opportunity_score_bps, index,
            deterministic_id("wallet-token-opportunity-ranking", identity),
        ))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class PersianCandidateExplanation:
    subject_id: str
    text: str
    explanation_id: str
    schema_version: str = "persian_candidate_explanation.v1"


@dataclass(frozen=True, slots=True)
class EvidenceConflictSurface:
    subject_id: str
    conflict_codes: tuple[str, ...]
    blocking_count: int
    has_blocking_conflict: bool
    surface_id: str
    schema_version: str = "evidence_conflict_surface.v1"


def build_evidence_conflict_surface(
    subject_id: str,
    conflicts: tuple[Mapping[str, object], ...],
) -> EvidenceConflictSurface:
    if not isinstance(subject_id, str) or not subject_id.strip():
        raise ValueError("subject_id must be non-empty")
    if not isinstance(conflicts, tuple) or not all(
        isinstance(item, Mapping) for item in conflicts
    ):
        raise TypeError("conflicts must be tuple of mappings")
    normalized: list[tuple[str, bool]] = []
    for item in conflicts:
        code = item.get("code")
        blocking = item.get("blocking")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("conflict code must be non-empty")
        if not isinstance(blocking, bool):
            raise TypeError("conflict blocking must be bool")
        normalized.append((code.strip(), blocking))
    if len({code for code, _ in normalized}) != len(normalized):
        raise ValueError("conflict codes must be unique")
    ordered = tuple(sorted(normalized))
    codes = tuple(code for code, _ in ordered)
    blocking_count = sum(blocking for _, blocking in ordered)
    identity = {
        "blocking_count": blocking_count,
        "conflicts": ordered,
        "schema_version": "evidence_conflict_surface.v1",
        "subject_id": subject_id.strip(),
    }
    return EvidenceConflictSurface(
        subject_id.strip(), codes, blocking_count, blocking_count > 0,
        deterministic_id("evidence-conflict-surface", identity),
    )


@dataclass(frozen=True, slots=True)
class HistoricalPerformanceSurface:
    subject_id: str
    sample_count: int
    validated_count: int
    failed_count: int
    success_rate_bps: int
    calibration_error_bps: int
    surface_id: str
    schema_version: str = "historical_performance_surface.v1"


def build_historical_performance_surface(
    subject_id: str,
    *,
    validated_count: int,
    failed_count: int,
    calibration_error_bps: int,
) -> HistoricalPerformanceSurface:
    if not isinstance(subject_id, str) or not subject_id.strip():
        raise ValueError("subject_id must be non-empty")
    values = (validated_count, failed_count, calibration_error_bps)
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values):
        raise ValueError("performance values must be non-negative integers")
    if calibration_error_bps > 10000:
        raise ValueError("calibration_error_bps must be at most 10000")
    sample_count = validated_count + failed_count
    if sample_count == 0:
        raise ValueError("historical performance requires samples")
    success_rate_bps = validated_count * 10000 // sample_count
    identity = {
        "calibration_error_bps": calibration_error_bps,
        "failed_count": failed_count,
        "schema_version": "historical_performance_surface.v1",
        "subject_id": subject_id.strip(),
        "validated_count": validated_count,
    }
    return HistoricalPerformanceSurface(
        subject_id.strip(), sample_count, validated_count, failed_count,
        success_rate_bps, calibration_error_bps,
        deterministic_id("historical-performance-surface", identity),
    )


@dataclass(frozen=True, slots=True)
class PersianAnalystDashboard:
    rankings: tuple[OpportunityRanking, ...]
    explanations: tuple[PersianCandidateExplanation, ...]
    conflicts: tuple[EvidenceConflictSurface, ...]
    performances: tuple[HistoricalPerformanceSurface, ...]
    blocked_subject_ids: tuple[str, ...]
    dashboard_id: str
    schema_version: str = "persian_analyst_dashboard.v1"


@dataclass(frozen=True, slots=True)
class ReleaseAuditEntry:
    sequence: int
    artifact_kind: str
    artifact_id: str
    previous_entry_id: str | None
    entry_id: str
    schema_version: str = "release_audit_entry.v1"


@dataclass(frozen=True, slots=True)
class ReleaseAuditChain:
    dashboard_id: str
    entries: tuple[ReleaseAuditEntry, ...]
    head_id: str
    chain_id: str
    schema_version: str = "release_audit_chain.v1"


def build_release_audit_chain(
    dashboard: PersianAnalystDashboard,
) -> ReleaseAuditChain:
    if not isinstance(dashboard, PersianAnalystDashboard):
        raise TypeError("dashboard must be PersianAnalystDashboard")
    artifacts = (
        ("dashboard", dashboard.dashboard_id),
        *((("ranking", item.ranking_id) for item in dashboard.rankings)),
        *((("explanation", item.explanation_id) for item in dashboard.explanations)),
        *((("conflict", item.surface_id) for item in dashboard.conflicts)),
        *((("performance", item.surface_id) for item in dashboard.performances)),
    )
    entries: list[ReleaseAuditEntry] = []
    previous: str | None = None
    for sequence, (artifact_kind, artifact_id) in enumerate(artifacts, start=1):
        identity = {
            "artifact_id": artifact_id,
            "artifact_kind": artifact_kind,
            "previous_entry_id": previous,
            "schema_version": "release_audit_entry.v1",
            "sequence": sequence,
        }
        entry_id = deterministic_id("release-audit-entry", identity)
        entries.append(
            ReleaseAuditEntry(
                sequence, artifact_kind, artifact_id, previous, entry_id
            )
        )
        previous = entry_id
    head_id = entries[-1].entry_id
    chain_identity = {
        "dashboard_id": dashboard.dashboard_id,
        "entry_ids": tuple(item.entry_id for item in entries),
        "head_id": head_id,
        "schema_version": "release_audit_chain.v1",
    }
    return ReleaseAuditChain(
        dashboard.dashboard_id,
        tuple(entries),
        head_id,
        deterministic_id("release-audit-chain", chain_identity),
    )


@dataclass(frozen=True, slots=True)
class EndToEndReplayReceipt:
    dashboard_id: str
    source_chain_id: str
    replay_chain_id: str
    source_head_id: str
    replay_head_id: str
    matches: bool
    receipt_id: str
    schema_version: str = "end_to_end_replay_receipt.v1"


def verify_release_replay(
    dashboard: PersianAnalystDashboard,
    source_chain: ReleaseAuditChain,
) -> EndToEndReplayReceipt:
    if not isinstance(dashboard, PersianAnalystDashboard):
        raise TypeError("dashboard must be PersianAnalystDashboard")
    if not isinstance(source_chain, ReleaseAuditChain):
        raise TypeError("source_chain must be ReleaseAuditChain")
    if source_chain.dashboard_id != dashboard.dashboard_id:
        raise ValueError("source chain does not belong to dashboard")
    replayed = build_release_audit_chain(dashboard)
    matches = (
        source_chain.chain_id == replayed.chain_id
        and source_chain.head_id == replayed.head_id
        and source_chain.entries == replayed.entries
    )
    identity = {
        "dashboard_id": dashboard.dashboard_id,
        "matches": matches,
        "replay_chain_id": replayed.chain_id,
        "replay_head_id": replayed.head_id,
        "schema_version": "end_to_end_replay_receipt.v1",
        "source_chain_id": source_chain.chain_id,
        "source_head_id": source_chain.head_id,
    }
    return EndToEndReplayReceipt(
        dashboard.dashboard_id,
        source_chain.chain_id,
        replayed.chain_id,
        source_chain.head_id,
        replayed.head_id,
        matches,
        deterministic_id("end-to-end-replay-receipt", identity),
    )


@dataclass(frozen=True, slots=True)
class ProductionIntelligenceReleaseGate:
    dashboard_id: str
    audit_chain_id: str
    replay_receipt_id: str
    checks: tuple[str, ...]
    passed_checks: tuple[str, ...]
    ready: bool
    gate_id: str
    schema_version: str = "production_intelligence_release_gate.v1"


def evaluate_production_intelligence_release(
    dashboard: PersianAnalystDashboard,
    audit_chain: ReleaseAuditChain,
    replay: EndToEndReplayReceipt,
) -> ProductionIntelligenceReleaseGate:
    if not isinstance(dashboard, PersianAnalystDashboard):
        raise TypeError("dashboard must be PersianAnalystDashboard")
    if not isinstance(audit_chain, ReleaseAuditChain):
        raise TypeError("audit_chain must be ReleaseAuditChain")
    if not isinstance(replay, EndToEndReplayReceipt):
        raise TypeError("replay must be EndToEndReplayReceipt")
    if (
        audit_chain.dashboard_id != dashboard.dashboard_id
        or replay.dashboard_id != dashboard.dashboard_id
        or replay.source_chain_id != audit_chain.chain_id
    ):
        raise ValueError("release artifacts are not bound to one dashboard")
    checks = (
        "dashboard_has_rankings",
        "historical_performance_present",
        "no_blocking_conflicts",
        "audit_chain_complete",
        "replay_verified",
    )
    passed_checks = tuple(
        name
        for name, passed in zip(
            checks,
            (
                bool(dashboard.rankings),
                bool(dashboard.performances),
                not dashboard.blocked_subject_ids,
                bool(audit_chain.entries) and audit_chain.head_id == audit_chain.entries[-1].entry_id,
                replay.matches,
            ),
        )
        if passed
    )
    ready = passed_checks == checks
    identity = {
        "audit_chain_id": audit_chain.chain_id,
        "checks": checks,
        "dashboard_id": dashboard.dashboard_id,
        "passed_checks": passed_checks,
        "ready": ready,
        "replay_receipt_id": replay.receipt_id,
        "schema_version": "production_intelligence_release_gate.v1",
    }
    return ProductionIntelligenceReleaseGate(
        dashboard.dashboard_id,
        audit_chain.chain_id,
        replay.receipt_id,
        checks,
        passed_checks,
        ready,
        deterministic_id("production-intelligence-release-gate", identity),
    )


def build_persian_analyst_dashboard(
    rankings: tuple[OpportunityRanking, ...],
    conflicts: tuple[EvidenceConflictSurface, ...],
    performances: tuple[HistoricalPerformanceSurface, ...],
) -> PersianAnalystDashboard:
    if not isinstance(rankings, tuple) or not rankings:
        raise ValueError("rankings must be a non-empty tuple")
    if not all(isinstance(item, OpportunityRanking) for item in rankings):
        raise TypeError("rankings must contain OpportunityRanking values")
    if not isinstance(conflicts, tuple) or not all(
        isinstance(item, EvidenceConflictSurface) for item in conflicts
    ):
        raise TypeError("conflicts must contain EvidenceConflictSurface values")
    if not isinstance(performances, tuple) or not all(
        isinstance(item, HistoricalPerformanceSurface) for item in performances
    ):
        raise TypeError("performances must contain HistoricalPerformanceSurface values")
    explanations = tuple(explain_opportunity_in_persian(item) for item in rankings)
    blocked = tuple(sorted(
        item.subject_id for item in conflicts if item.has_blocking_conflict
    ))
    identity = {
        "conflict_ids": tuple(sorted(item.surface_id for item in conflicts)),
        "performance_ids": tuple(sorted(item.surface_id for item in performances)),
        "ranking_ids": tuple(item.ranking_id for item in rankings),
        "schema_version": "persian_analyst_dashboard.v1",
    }
    return PersianAnalystDashboard(
        rankings, explanations, conflicts, performances, blocked,
        deterministic_id("persian-analyst-dashboard", identity),
    )


def explain_opportunity_in_persian(
    ranking: OpportunityRanking,
) -> PersianCandidateExplanation:
    if not isinstance(ranking, OpportunityRanking):
        raise TypeError("ranking must be OpportunityRanking")
    text = (
        f"کاندید {ranking.subject_id} رتبهٔ {ranking.rank} دارد. "
        f"امتیاز رفتار ولت {ranking.wallet_score_bps} و امتیاز ایمنی توکن "
        f"{ranking.token_safety_bps} واحد پایه است؛ امتیاز ترکیبی "
        f"{ranking.opportunity_score_bps} واحد پایه محاسبه شد. "
        "این توضیح صرفاً بر پایهٔ Evidence است و توصیهٔ معامله نیست."
    )
    identity = {
        "ranking_id": ranking.ranking_id,
        "schema_version": "persian_candidate_explanation.v1",
        "subject_id": ranking.subject_id,
        "text": text,
    }
    return PersianCandidateExplanation(
        ranking.subject_id, text,
        deterministic_id("persian-candidate-explanation", identity),
    )


__all__ = [
    "TokenSafetyProductionProfile",
    "build_token_safety_production_profile",
    "OpportunityRanking",
    "rank_wallet_token_opportunities",
    "PersianCandidateExplanation",
    "explain_opportunity_in_persian",
    "EvidenceConflictSurface",
    "build_evidence_conflict_surface",
    "HistoricalPerformanceSurface",
    "build_historical_performance_surface",
    "PersianAnalystDashboard",
    "build_persian_analyst_dashboard",
    "ReleaseAuditEntry",
    "ReleaseAuditChain",
    "build_release_audit_chain",
    "EndToEndReplayReceipt",
    "verify_release_replay",
    "ProductionIntelligenceReleaseGate",
    "evaluate_production_intelligence_release",
]
