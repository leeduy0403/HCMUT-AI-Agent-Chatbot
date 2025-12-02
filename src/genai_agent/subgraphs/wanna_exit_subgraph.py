from langgraph.graph import StateGraph, END
from ..nodes.subgraph.wanna_exit_nodes import wanna_exit_node
from ..nodes.reset_topic import reset_topic_node
from ..states.agent_state import AgentState

def build_wanna_exit_subgraph():
    graph = StateGraph(AgentState)
    graph.add_node("wanna_exit_node", wanna_exit_node)
    graph.add_node("reset_topic_node", reset_topic_node)

    graph.set_entry_point("wanna_exit_node") # START -> exit_node
    graph.add_edge("wanna_exit_node", "reset_topic_node") # exit_node -> reset_topic_node
    graph.add_edge("reset_topic_node", END) # reset_topic_node -> END

    return graph.compile()