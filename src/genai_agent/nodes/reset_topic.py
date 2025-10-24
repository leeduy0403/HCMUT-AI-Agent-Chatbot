from ..states.agent_state import AgentState

def reset_topic_node(state: AgentState):
    return {
        "topic": None,
    }