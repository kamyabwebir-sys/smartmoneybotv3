from smart_money.application.opportunity_evidence_graph import OpportunityGraphNode, OpportunityNodeKind, OpportunityGraphEdge, OpportunityEdgeKind, project_opportunity_graph
from smart_money.application.opportunity_graph_pipeline import OpportunityGraphStore
from smart_money.application.opportunity_graph_dashboard import OpportunityGraphAuditStore, read_opportunity_graph_dashboard
from smart_money.core.ids import deterministic_id

def test_graph_audit_persistence_dashboard(tmp_path) -> None:
    a=OpportunityGraphNode("w",OpportunityNodeKind.WALLET,"w")
    b=OpportunityGraphNode("t",OpportunityNodeKind.TOKEN,"t")
    i={"evidence_ids":("e",),"kind":"WALLET_OBSERVED_TOKEN","schema_version":"opportunity_graph_edge.v1","source_node_id":"w","target_node_id":"t"}
    edge=OpportunityGraphEdge(deterministic_id("opportunity_graph_edge",i),"w","t",OpportunityEdgeKind.WALLET_OBSERVED_TOKEN,("e",))
    graph,_=project_opportunity_graph((a,b),(edge,))
    store=OpportunityGraphStore(tmp_path/"graph.json")
    store.save(graph)
    read=read_opportunity_graph_dashboard(store,graph.graph_id)
    audits=OpportunityGraphAuditStore(tmp_path/"audit.json")
    audits.save(read.audit)
    assert audits.get(read.audit.audit_id)==read.audit
