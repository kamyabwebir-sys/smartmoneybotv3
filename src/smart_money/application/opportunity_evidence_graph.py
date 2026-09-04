from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload


class OpportunityNodeKind(str, Enum):
    WALLET = "WALLET"
    TOKEN = "TOKEN"
    CANDIDATE = "CANDIDATE"


@dataclass(frozen=True, slots=True)
class OpportunityGraphNode:
    node_id: str
    kind: OpportunityNodeKind
    label: str
    schema_version: str = "opportunity_graph_node.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise ValueError("node_id must be non-empty")
        if not isinstance(self.kind, OpportunityNodeKind):
            raise TypeError("kind must be OpportunityNodeKind")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("label must be non-empty")

    def canonical_dict(self) -> dict[str, Any]:
        return {"node_id": self.node_id.strip(), "kind": self.kind.value,
                "label": self.label.strip(), "schema_version": self.schema_version}


class OpportunityEdgeKind(str, Enum):
    WALLET_OBSERVED_TOKEN = "WALLET_OBSERVED_TOKEN"
    CANDIDATE_REFERENCES_WALLET = "CANDIDATE_REFERENCES_WALLET"
    CANDIDATE_REFERENCES_TOKEN = "CANDIDATE_REFERENCES_TOKEN"


@dataclass(frozen=True, slots=True)
class OpportunityGraphEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    kind: OpportunityEdgeKind
    evidence_ids: tuple[str, ...]
    schema_version: str = "opportunity_graph_edge.v1"

    def __post_init__(self) -> None:
        if not self.source_node_id.strip() or not self.target_node_id.strip():
            raise ValueError("edge endpoints must be non-empty")
        if not isinstance(self.kind, OpportunityEdgeKind):
            raise TypeError("kind must be OpportunityEdgeKind")
        if not isinstance(self.evidence_ids, tuple) or not self.evidence_ids:
            raise ValueError("evidence_ids must be non-empty")
        if self.edge_id != deterministic_id("opportunity_graph_edge", self.identity_payload()):
            raise ValueError("edge_id mismatch")

    def identity_payload(self) -> dict[str, Any]:
        return {"evidence_ids": self.evidence_ids, "kind": self.kind.value,
                "schema_version": self.schema_version,
                "source_node_id": self.source_node_id.strip(),
                "target_node_id": self.target_node_id.strip()}

    def canonical_dict(self) -> dict[str, Any]:
        return {"edge_id": self.edge_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class OpportunityEvidenceGraph:
    nodes: tuple[OpportunityGraphNode, ...]
    edges: tuple[OpportunityGraphEdge, ...]
    graph_id: str
    schema_version: str = "opportunity_evidence_graph.v1"

    def __post_init__(self) -> None:
        expected = deterministic_id("opportunity_evidence_graph", {
            "edges": tuple(x.canonical_dict() for x in self.edges),
            "nodes": tuple(x.canonical_dict() for x in self.nodes),
            "schema_version": self.schema_version,
        })
        if self.graph_id != expected:
            raise ValueError("graph_id mismatch")

    def canonical_dict(self) -> dict[str, Any]:
        return {"edges": [x.canonical_dict() for x in self.edges],
                "graph_id": self.graph_id, "nodes": [x.canonical_dict() for x in self.nodes],
                "schema_version": self.schema_version}


def project_opportunity_graph(nodes: tuple[OpportunityGraphNode, ...],
                              edges: tuple[OpportunityGraphEdge, ...]) -> tuple[OpportunityEvidenceGraph, EvidencePayload]:
    identity = {"edges": tuple(x.canonical_dict() for x in edges),
                "nodes": tuple(x.canonical_dict() for x in nodes),
                "schema_version": "opportunity_evidence_graph.v1"}
    graph = OpportunityEvidenceGraph(nodes, edges, deterministic_id("opportunity_evidence_graph", identity))
    payload = EvidencePayload(source_id="opportunity-graph", evidence_type="opportunity_evidence_graph",
                              data={"graph": graph.canonical_dict()},
                              metadata={"authority": "NONE", "classification": "EVIDENCE",
                                        "verification_status": "UNKNOWN",
                                        "provenance": {"graph_id": graph.graph_id}})
    return graph, payload


def query_opportunity_graph(graph: OpportunityEvidenceGraph, *, kind: OpportunityNodeKind | None = None,
                            label: str | None = None) -> tuple[OpportunityGraphNode, ...]:
    if not isinstance(graph, OpportunityEvidenceGraph):
        raise TypeError("graph must be OpportunityEvidenceGraph")
    return tuple(node for node in graph.nodes if
                 (kind is None or node.kind is kind) and
                 (label is None or node.label == label.strip()))


def verify_opportunity_graph_replay(graph: OpportunityEvidenceGraph,
                                    payload: EvidencePayload) -> bool:
    if not isinstance(payload, EvidencePayload):
        raise TypeError("payload must be EvidencePayload")
    retained = payload.data.get("graph")
    return (
        payload.evidence_type == "opportunity_evidence_graph"
        and hasattr(retained, "get")
        and retained.get("graph_id") == graph.graph_id
    )


__all__ = ["OpportunityNodeKind", "OpportunityGraphNode", "OpportunityEdgeKind",
           "OpportunityGraphEdge", "OpportunityEvidenceGraph", "project_opportunity_graph",
           "query_opportunity_graph", "verify_opportunity_graph_replay"]
