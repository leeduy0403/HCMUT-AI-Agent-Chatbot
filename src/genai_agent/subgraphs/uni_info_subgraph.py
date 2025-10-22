from langgraph.graph import StateGraph, END
from ..nodes.subgraph.uni_info_nodes import uni_info_node
from ..nodes.reset_topic import reset_topic_node
from ..states.sales_agent_state import SalesAgentState

def build_uni_info_subgraph():
    graph = StateGraph(SalesAgentState)
    graph.add_node("uni_info_node", uni_info_node)
    graph.add_node("reset_topic_node", reset_topic_node)

    graph.set_entry_point("uni_info_node") # START -> uni_info_node
    graph.add_edge("uni_info_node", "reset_topic_node") # uni_info_node -> reset_topic_node
    graph.add_edge("reset_topic_node", END) # reset_topic_node -> END

    return graph.compile()