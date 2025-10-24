from langgraph.graph import StateGraph, END
from ..nodes.subgraph.tuition_fee_nodes import tuition_fee_node
from ..nodes.reset_topic import reset_topic_node
from ..states.agent_state import AgentState

def build_tuition_fee_subgraph():
    graph = StateGraph(AgentState)
    graph.add_node("tuition_fee_node", tuition_fee_node)
    graph.add_node("reset_topic_node", reset_topic_node)

    graph.set_entry_point("tuition_fee_node") # START -> tuition_fee_node
    graph.add_edge("tuition_fee_node", "reset_topic_node") # tuition_fee_node -> reset_topic_node
    graph.add_edge("reset_topic_node", END) # reset_topic_node -> END

    return graph.compile()