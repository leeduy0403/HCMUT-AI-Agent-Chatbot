import os
from dotenv import load_dotenv, find_dotenv
from langgraph.graph import StateGraph, END
from .states.agent_state import AgentState
from .nodes.router import router_node
from .nodes.flow_controller import flow_controller_node, get_selected_flow
from .nodes.do_nothing import do_nothing_node
from .subgraphs.greeting_subgraph import build_greeting_subgraph
from .subgraphs.off_topic_subgraph import build_off_topic_subgraph
from .subgraphs.uni_info_subgraph import build_uni_info_subgraph
from .subgraphs.undergraduate_subgraph import build_undergraduate_subgraph
from .subgraphs.graduate_subgraph import build_graduate_subgraph
from .subgraphs.tuition_fee_subgraph import build_tuition_fee_subgraph
from .subgraphs.regulation_info_subgraph import build_regulation_info_subgraph
from .subgraphs.wanna_exit_subgraph import build_wanna_exit_subgraph

from langgraph.checkpoint.memory import MemorySaver


load_dotenv(find_dotenv())

SUBGRAPH_PATH_MAP = {
    'greeting': 'greeting_subgraph',
    'off_topic': 'off_topic_subgraph',
    'university_info': 'uni_info_subgraph',
    'undergraduate_info': 'undergraduate_subgraph',
    'graduate_info': 'graduate_subgraph',
    'tuition_fee_info': 'tuition_fee_subgraph',
    'regulation_info': 'regulation_info_subgraph',
    'wanna_exit': 'wanna_exit_subgraph',
}

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("router_node", router_node)
    graph.add_node("flow_controller_node", flow_controller_node)
    graph.add_node("greeting_subgraph", build_greeting_subgraph())
    graph.add_node("off_topic_subgraph", build_off_topic_subgraph())
    graph.add_node("uni_info_subgraph", build_uni_info_subgraph())
    graph.add_node("undergraduate_subgraph", build_undergraduate_subgraph())
    graph.add_node("graduate_subgraph", build_graduate_subgraph())
    graph.add_node("tuition_fee_subgraph", build_tuition_fee_subgraph())
    graph.add_node("regulation_info_subgraph", build_regulation_info_subgraph())
    graph.add_node("wanna_exit_subgraph", build_wanna_exit_subgraph())

    # graph.add_node("do_nothing_node", do_nothing_node)

    graph.set_entry_point("router_node") # START -> router_node
    graph.add_edge("router_node", "flow_controller_node") # router_node -> flow_controller_node

    graph.add_conditional_edges(
        "flow_controller_node",
        get_selected_flow,
        SUBGRAPH_PATH_MAP
    )

    # Memory
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)

    