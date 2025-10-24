from langgraph.graph import StateGraph, END
from ..nodes.subgraph.undergraduate_nodes import undergraduate_node
from ..nodes.reset_topic import reset_topic_node
from ..states.agent_state import AgentState

def build_undergraduate_subgraph():
    graph = StateGraph(AgentState)
    graph.add_node("undergraduate_node", undergraduate_node)
    graph.add_node("reset_topic_node", reset_topic_node)

    graph.set_entry_point("undergraduate_node") # START -> undergraduate_node
    graph.add_edge("undergraduate_node", "reset_topic_node") # undergraduate_node -> reset_topic_node
    graph.add_edge("reset_topic_node", END) # reset_topic_node -> END

    return graph.compile()