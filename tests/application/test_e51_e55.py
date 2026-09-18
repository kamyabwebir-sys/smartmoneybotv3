from smart_money.application.opportunity_evidence_graph import (
    OpportunityEdgeKind, OpportunityGraphEdge, OpportunityGraphNode, OpportunityNodeKind,
    project_opportunity_graph, query_opportunity_graph, verify_opportunity_graph_replay,
)
from smart_money.core.ids import deterministic_id


def test_opportunity_graph_projection_query_replay() -> None:
    wallet = OpportunityGraphNode("w", OpportunityNodeKind.WALLET, "w")
    token = OpportunityGraphNode("t", OpportunityNodeKind.TOKEN, "t")
    identity = {"evidence_ids": ("e1",), "kind": OpportunityEdgeKind.WALLET_OBSERVED_TOKEN.value,
                "schema_version": "opportunity_graph_edge.v1", "source_node_id": "w", "target_node_id": "t"}
    edge = OpportunityGraphEdge(deterministic_id("opportunity_graph_edge", identity), "w", "t",
                                OpportunityEdgeKind.WALLET_OBSERVED_TOKEN, ("e1",))
    graph, payload = project_opportunity_graph((wallet, token), (edge,))
    assert len(query_opportunity_graph(graph, kind=OpportunityNodeKind.WALLET)) == 1
    assert verify_opportunity_graph_replay(graph, payload)
