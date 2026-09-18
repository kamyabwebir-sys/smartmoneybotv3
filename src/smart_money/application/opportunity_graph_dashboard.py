from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from smart_money.application.opportunity_evidence_graph import OpportunityEvidenceGraph
from smart_money.application.opportunity_graph_pipeline import OpportunityGraphStore
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class OpportunityGraphQueryAudit:
    graph_id: str
    result_count: int
    audit_id: str
    schema_version: str = "opportunity_graph_query_audit.v1"
    def __post_init__(self) -> None:
        expected = deterministic_id("opportunity_graph_query_audit", {"graph_id":self.graph_id,"result_count":self.result_count,"schema_version":self.schema_version})
        if self.audit_id != expected:
            raise ValueError("audit_id mismatch")

def build_opportunity_graph_query_audit(graph: OpportunityEvidenceGraph) -> OpportunityGraphQueryAudit:
    if not isinstance(graph, OpportunityEvidenceGraph):
        raise TypeError("graph must be OpportunityEvidenceGraph")
    identity={"graph_id":graph.graph_id,"result_count":len(graph.nodes),"schema_version":"opportunity_graph_query_audit.v1"}
    return OpportunityGraphQueryAudit(graph.graph_id,len(graph.nodes),deterministic_id("opportunity_graph_query_audit",identity))

class OpportunityGraphAuditStore:
    def __init__(self, path: str | Path) -> None:
        self.path=Path(path)
        self._items: dict[str, OpportunityGraphQueryAudit] = {}
    def save(self, audit: OpportunityGraphQueryAudit) -> str:
        if not isinstance(audit, OpportunityGraphQueryAudit):
            raise TypeError("audit must be OpportunityGraphQueryAudit")
        self._items[audit.audit_id]=audit
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"opportunity_graph_audit_store.v1","items":[{"graph_id":x.graph_id,"result_count":x.result_count,"audit_id":x.audit_id,"schema_version":x.schema_version} for x in self._items.values()]},sort_keys=True,separators=(",",":")),encoding="utf-8")
        return audit.audit_id
    def get(self, audit_id: str) -> OpportunityGraphQueryAudit | None:
        return self._items.get(audit_id)

@dataclass(frozen=True, slots=True)
class OpportunityGraphDashboardRead:
    graph: OpportunityEvidenceGraph
    audit: OpportunityGraphQueryAudit
    schema_version: str = "opportunity_graph_dashboard_read.v1"

def read_opportunity_graph_dashboard(store: OpportunityGraphStore, graph_id: str) -> OpportunityGraphDashboardRead:
    if not isinstance(store, OpportunityGraphStore):
        raise TypeError("store must be OpportunityGraphStore")
    graph=store.get(graph_id)
    if graph is None:
        raise KeyError("opportunity graph not found")
    return OpportunityGraphDashboardRead(graph, build_opportunity_graph_query_audit(graph))

__all__=["OpportunityGraphQueryAudit","build_opportunity_graph_query_audit","OpportunityGraphAuditStore","OpportunityGraphDashboardRead","read_opportunity_graph_dashboard"]
