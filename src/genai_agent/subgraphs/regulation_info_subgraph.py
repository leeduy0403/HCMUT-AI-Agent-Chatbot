from langgraph.graph import StateGraph, END
from ..nodes.subgraph.regulation_info_nodes import regulation_info_node
from ..nodes.reset_topic import reset_topic_node
from ..states.agent_state import AgentState

def build_regulation_info_subgraph():
    graph = StateGraph(AgentState)
    graph.add_node("regulation_info_node", regulation_info_node)
    graph.add_node("reset_topic_node", reset_topic_node)

    graph.set_entry_point("regulation_info_node") # START -> regulation_info_node
    graph.add_edge("regulation_info_node", "reset_topic_node") # regulation_info_node -> reset_topic_node
    graph.add_edge("reset_topic_node", END) # reset_topic_node -> END

    return graph.compile()