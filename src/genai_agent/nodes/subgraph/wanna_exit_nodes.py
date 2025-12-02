import os
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from langchain_core.messages import AIMessage
from litellm import completion
from logger import logger
from ...states.agent_state import AgentState
from ...utils.helpers import parsing_messages_to_history, remove_think_tag
from ...utils.const_prompts import (
    CONST_ASSISTANT_ROLE,
    CONST_ASSISTANT_TONE,
    CONST_FORM_ADDRESS_IN_VN
)
from config import LLM_MODELS

load_dotenv(find_dotenv())

def wanna_exit_node(state: AgentState):
    logger.info("wanna_exit_node called.")
    user_input = state['messages'][-1].content
    chat_history = parsing_messages_to_history(state.get('messages', ''))

    prompt = f"""
    # Role
    {CONST_ASSISTANT_ROLE}

    # Tone
    {CONST_ASSISTANT_TONE}

    # Tasks
    - The user wants to end the conversation or say goodbye.
    - The Assistant MUST politely say goodbye to the user.
    - Wish the user a good day or success in their studies.

    # Constraints
    - Keep the answer concise (under 50 words).
    - Assistant MUST use the same language as the User's language to reply.
    {CONST_FORM_ADDRESS_IN_VN}

    Chat History:
    ```
    {chat_history}
    ```

    User's input: {user_input}
    Answer:
    """

    try:
        response = completion(
            api_key=os.getenv("GROQ_API_KEY"),
            model=LLM_MODELS['wanna_exit_subgraph']['wanna_exit_node'],
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )
        content = remove_think_tag(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error in wanna_exit_node: {e}")
        content = "Tạm biệt bạn! Xin hẹn gặp lại."

    ai_message = AIMessage(
        content=content,
        additional_kwargs={"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    )

    return {
        "messages": ai_message,
        "ai_reply": ai_message
    }