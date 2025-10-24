from langgraph.graph import StateGraph, END
from ..nodes.subgraph.graduate_nodes import graduate_node
from ..nodes.reset_topic import reset_topic_node
from ..states.agent_state import AgentState

def build_graduate_subgraph():
    graph = StateGraph(AgentState)
    graph.add_node("graduate_node", graduate_node)
    graph.add_node("reset_topic_node", reset_topic_node)

    graph.set_entry_point("graduate_node") # START -> graduate_node
    graph.add_edge("graduate_node", "reset_topic_node") # graduate_node -> reset_topic_node
    graph.add_edge("reset_topic_node", END) # reset_topic_node -> END

    return graph.compile()