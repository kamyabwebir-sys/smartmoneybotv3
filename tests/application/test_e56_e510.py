from smart_money.application.opportunity_evidence_graph import OpportunityGraphNode, OpportunityNodeKind, OpportunityGraphEdge, OpportunityEdgeKind, project_opportunity_graph
from smart_money.core.ids import deterministic_id
from smart_money.application.opportunity_graph_pipeline import OpportunityGraphStore, build_opportunity_graph_audit, ingest_opportunity_graph, rank_opportunity_graphs, verify_opportunity_graph_store
from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger

def test_opportunity_graph_pipeline(tmp_path) -> None:
    node_a = OpportunityGraphNode("w", OpportunityNodeKind.WALLET, "w")
    node_b = OpportunityGraphNode("t", OpportunityNodeKind.TOKEN, "t")
    edge_identity = {"evidence_ids": ("e",), "kind": "WALLET_OBSERVED_TOKEN", "schema_version": "opportunity_graph_edge.v1", "source_node_id": "w", "target_node_id": "t"}
    edge = OpportunityGraphEdge(deterministic_id("opportunity_graph_edge", edge_identity), "w", "t", OpportunityEdgeKind.WALLET_OBSERVED_TOKEN, ("e",))
    graph_fixture, _ = project_opportunity_graph((node_a, node_b), (edge,))
    ledger = EvidenceGroundingLedger()
    receipt = ingest_opportunity_graph(graph_fixture, ledger)
    store = OpportunityGraphStore(tmp_path / "graph.json")
    store.save(graph_fixture)
    replay = verify_opportunity_graph_store(graph_fixture, store)
    audit = build_opportunity_graph_audit(graph_fixture, receipt, replay)
    assert receipt.evidence_id and replay.matches and audit.audit_id
    assert rank_opportunity_graphs((graph_fixture,))[0].rank == 1
