from ..states.agent_state import AgentState
from logger import logger
def do_nothing_node(state: AgentState):
    logger.info("do_nothing_node called.")
    return {}