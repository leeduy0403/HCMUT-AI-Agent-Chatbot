import os
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from langchain_core.messages import AIMessage
from ...states.agent_state import AgentState
from litellm import completion
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
from ...vector_db.pinecone_store import PineconeStore  
from ...utils.rag_formatter import RAGResponseFormatter 



os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
load_dotenv(find_dotenv())

# --- Initialize vector store connection once ---
try:
    vector_store = PineconeStore()
except Exception as e:
    logger.error(f"❌ Error initializing vector store: {e}")
    vector_store = None


load_dotenv(find_dotenv())

openai.api_key = os.environ["OPENAI_API_KEY"]

def regulation_info_node(state: AgentState):
    logger.info("regulation_info_node called.")

    if vector_store is None or not vector_store.is_healthy():
        error_msg = "Lỗi: Kết nối RAG không khả dụng."
        logger.error(error_msg)
        return {
            "messages": AIMessage(content=error_msg),
            "ai_reply": AIMessage(content=error_msg)
        }
    
    user_input = state['messages'][-1].content
    chat_history = parsing_messages_to_history(state.get('messages', ''))

     # --- 1. RAG Retrieval Step (This is now clean) ---
    logger.info("Retrieving context from vector store...")
    context = "Không tìm thấy thông tin liên quan." # Default context
    matches = [] # Default matches

    try:
        matches = vector_store.query(
            query_text=user_input,
            topic="regulation_info",
            k=3
        )
        
        if not matches:
            logger.warning("No relevant context found")
            context = "Không tìm thấy thông tin liên quan."
        else:
            # Sort matches by score and combine content
            context = "\n\n".join(m['content'] for m in matches)
            logger.info(f"Retrieved {len(matches)} reranked matches with scores: " +
                        ", ".join(f"{m['score']:.3f}" for m in matches))
            
        logger.debug(f"--- CONTEXT SẼ GỬI ĐẾN LLM ---\n{context}\n--- HẾT CONTEXT ---")

    except Exception as e:
        logger.error(f"❌ Error during RAG query: {e}")
        context = "Lỗi: Không thể truy xuất thông tin về các quy định."
    
    system_prompts = {
        "ROLE": CONST_ASSISTANT_ROLE,
        "SKILLS": CONST_ASSISTANT_SKILLS,
        "TONE": CONST_ASSISTANT_TONE,
        "TASKS": "If the user asks about academic regulations, examinations,  leave of absence, academic warning, or other student policies, provide accurate and detailed information based on {CONST_UNIVERSITY_NAME}'s official regulations from the knowledge base.",
        "EXAMPLES": f"""
                        None
        """,

        "CONSTRAINTS": f""" 
                        - Assistant's works MUST be formatted in an easy to read manner. Highly recommend list in bullet point format.
                        - Keep the answers concise and under 200 words.
                        - Assistant MUST use the same language as the User's language to reply.   
                        {CONST_FORM_ADDRESS_IN_VN}
        """,
        "IMPORTANT_INFORMATION": f"""
    - 1 academic year = 2 semesters (1 năm học = 2 học kỳ).
    - Pay attention to the abbreviations that have been explained in the document to better understand the user input."""
        
    }
   
    final_prompt = RAGResponseFormatter.format_prompt(
        user_input=user_input,
        retrieved_context=context,
        chat_history=chat_history,
        system_prompts=system_prompts
    )
    
    # (Optional) Format the sources to pass to the UI
    source_info = RAGResponseFormatter.format_sources(matches)

    try:
        response = completion(
            api_key=os.getenv("GROQ_API_KEY"),
            model=LLM_MODELS['regulation_info_subgraph']['regulation_info_node'],
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.3
        )
        final_answer = response.choices[0].message.content
        final_answer = remove_think_tag(final_answer)
    except Exception as e:
        logger.error(f"❌ Error during Groq API call: {e}")
        final_answer = "Xin lỗi, tôi đã gặp lỗi khi tạo câu trả lời."

     # --- 4. Return State ---
    ai_message = AIMessage(
        content=final_answer,
        additional_kwargs={
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources": source_info  # 
        }
    )

    return {
        "messages": ai_message,
        "ai_reply": ai_message
    }