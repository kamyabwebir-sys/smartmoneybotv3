from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from smart_money.application.opportunity_evidence_graph import OpportunityEvidenceGraph, project_opportunity_graph
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class OpportunityGraphLedgerReceipt:
    graph_id: str
    evidence_id: str
    already_present: bool

def ingest_opportunity_graph(graph: OpportunityEvidenceGraph, ledger: EvidenceLedger) -> OpportunityGraphLedgerReceipt:
    if not isinstance(graph, OpportunityEvidenceGraph) or not isinstance(ledger, EvidenceLedger):
        raise TypeError("invalid graph or ledger")
    _, payload = project_opportunity_graph(graph.nodes, graph.edges)
    evidence_id = payload.get_canonical_id()
    present = ledger.contains(evidence_id)
    if ledger.append(payload) != evidence_id:
        raise ValueError("ledger identity mismatch")
    return OpportunityGraphLedgerReceipt(graph.graph_id, evidence_id, present)

class OpportunityGraphStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, OpportunityEvidenceGraph] = {}
    def save(self, graph: OpportunityEvidenceGraph) -> str:
        if not isinstance(graph, OpportunityEvidenceGraph):
            raise TypeError("graph must be OpportunityEvidenceGraph")
        self._items[graph.graph_id] = graph
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"opportunity_graph_store.v1","items":[g.canonical_dict() for g in self._items.values()]}, sort_keys=True, separators=(",",":")), encoding="utf-8")
        return graph.graph_id
    def get(self, graph_id: str) -> OpportunityEvidenceGraph | None:
        return self._items.get(graph_id)

@dataclass(frozen=True, slots=True)
class OpportunityGraphStoreReplayVerification:
    graph_id: str
    matches: bool
    verification_id: str
    schema_version: str = "opportunity_graph_store_replay.v1"

def verify_opportunity_graph_store(graph: OpportunityEvidenceGraph, store: OpportunityGraphStore) -> OpportunityGraphStoreReplayVerification:
    if not isinstance(graph, OpportunityEvidenceGraph) or not isinstance(store, OpportunityGraphStore):
        raise TypeError("invalid graph or store")
    matches = store.get(graph.graph_id) == graph
    identity = {"graph_id": graph.graph_id, "matches": matches, "schema_version":"opportunity_graph_store_replay.v1"}
    return OpportunityGraphStoreReplayVerification(graph.graph_id, matches, deterministic_id("opportunity_graph_store_replay", identity))

@dataclass(frozen=True, slots=True)
class OpportunityGraphRanked:
    graph_id: str
    rank: int
    score: int

def rank_opportunity_graphs(graphs: tuple[OpportunityEvidenceGraph, ...]) -> tuple[OpportunityGraphRanked, ...]:
    if not isinstance(graphs, tuple) or not all(isinstance(g, OpportunityEvidenceGraph) for g in graphs):
        raise TypeError("graphs must be tuple of OpportunityEvidenceGraph")
    ordered = sorted(graphs, key=lambda g: g.graph_id)
    return tuple(OpportunityGraphRanked(g.graph_id, i, len(ordered)-i+1) for i, g in enumerate(ordered, 1))

@dataclass(frozen=True, slots=True)
class OpportunityGraphAuditReceipt:
    graph_id: str
    evidence_id: str
    replay_verified: bool
    audit_id: str
    schema_version: str = "opportunity_graph_audit.v1"
    def __post_init__(self) -> None:
        identity = {"evidence_id":self.evidence_id,"graph_id":self.graph_id,"replay_verified":self.replay_verified,"schema_version":self.schema_version}
        if self.audit_id != deterministic_id("opportunity_graph_audit", identity):
            raise ValueError("audit_id mismatch")
    def canonical_dict(self) -> dict[str, object]:
        return {"audit_id":self.audit_id,"evidence_id":self.evidence_id,"graph_id":self.graph_id,"replay_verified":self.replay_verified,"schema_version":self.schema_version}

def build_opportunity_graph_audit(graph: OpportunityEvidenceGraph, receipt: OpportunityGraphLedgerReceipt, replay: OpportunityGraphStoreReplayVerification) -> OpportunityGraphAuditReceipt:
    return OpportunityGraphAuditReceipt(graph.graph_id, receipt.evidence_id, replay.matches, deterministic_id("opportunity_graph_audit", {"evidence_id":receipt.evidence_id,"graph_id":graph.graph_id,"replay_verified":replay.matches,"schema_version":"opportunity_graph_audit.v1"}))

__all__ = ["OpportunityGraphLedgerReceipt","OpportunityGraphStore","OpportunityGraphStoreReplayVerification","verify_opportunity_graph_store","OpportunityGraphRanked","rank_opportunity_graphs","OpportunityGraphAuditReceipt","build_opportunity_graph_audit","ingest_opportunity_graph"]
