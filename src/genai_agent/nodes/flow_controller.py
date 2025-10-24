from ..states.agent_state import AgentState
from logger import logger

TOPIC_FLOW_MAPPING = {
    "greeting": "greeting",
    "off_topic": "off_topic",
    "university_info": "university_info",
    "undergraduate_info": "undergraduate_info",
    "graduate_info": "graduate_info",
    "tuition_fee_info": "tuition_fee_info",
    "regulation_info": "regulation_info",
    "wanna_exit": "wanna_exit"
}

def flow_controller_node(state: AgentState):
    selected_flow = TOPIC_FLOW_MAPPING[state['topic'].name]
    logger.info(f"Selected Flow: {selected_flow}")

    return {
        "selected_flow": selected_flow
    }

def get_selected_flow(state: AgentState):
    return state.get('selected_flow', TOPIC_FLOW_MAPPING['off_topic'])