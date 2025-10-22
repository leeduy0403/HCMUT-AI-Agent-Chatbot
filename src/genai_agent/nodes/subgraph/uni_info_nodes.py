import os
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from langchain_core.messages import AIMessage
from ...states.sales_agent_state import SalesAgentState
import openai
from logger import logger
from ...utils.helpers import parsing_messages_to_history, remove_think_tag
from ...utils.const_prompts import (
    CONST_ASSISTANT_NAME,
    CONST_UNIVERSITY_NAME,
    CONST_UNIVERSITY_HOTLINE,
    CONST_FACULTIES,
    CONST_ASSISTANT_ROLE,
    CONST_ASSISTANT_SKILLS,
    CONST_ASSISTANT_TONE,
    CONST_FORM_ADDRESS_IN_VN,
    CONST_ASSISTANT_SCOPE_OF_WORK,
    CONST_ASSISTANT_PRIME_JOB
)
from config import LLM_MODELS

load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]

def uni_info_node(state: SalesAgentState):
    logger.info("uni_info_node called.")
    user_input = state['messages'][-1].content
    chat_history = parsing_messages_to_history(state.get('messages', ''))

    prompt = f"""
    # Role
    {CONST_ASSISTANT_ROLE}

    # Skills
    {CONST_ASSISTANT_SKILLS}

    # Tone
    {CONST_ASSISTANT_TONE}

    # Tasks
    - If the user asks for general information about the university such as its history, address, campuses, contact details, vision, mission, achievements, organizational structure, or faculties, the Assistant must provide the corresponding information of {CONST_UNIVERSITY_NAME}.
    
    # Constraints
    - Assistant's works MUST be formatted in an easy to read manner. Highly recommend list in bullet point format.
    - Keep the answers concise and under 200 words.
    - Assistant MUST use the same language as the User's language to reply.   
    {CONST_FORM_ADDRESS_IN_VN}

    Chat History:
    ```
    {chat_history}
    ```

    User's input: {user_input}
    Answer:
    """

    response = openai.chat.completions.create(
        model=LLM_MODELS['llm_subgraph']['llm_node'],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    ai_message = AIMessage(
        content=remove_think_tag(response.choices[0].message.content),
        additional_kwargs={"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    )

    return {
        "messages": ai_message,
        "ai_reply": ai_message
    }