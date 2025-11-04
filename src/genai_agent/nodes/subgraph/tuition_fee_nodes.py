import os
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from litellm import completion
from langchain_core.messages import AIMessage
from logger import logger
from ...states.agent_state import AgentState
from ...utils.helpers import parsing_messages_to_history, remove_think_tag
from config import LLM_MODELS
from ...vector_db.pinecone_store import PineconeStore  
from ...utils.rag_formatter import RAGResponseFormatter 

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



os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
load_dotenv(find_dotenv())

# Initialize vector store connection 
try:
    vector_store = PineconeStore()
except Exception as e:
    logger.error(f"❌ Error initializing vector store: {e}")
    vector_store = None


def tuition_fee_node(state: AgentState):
    logger.info("tuition_fee_node called.")
    
    if vector_store is None or not vector_store.is_healthy():
        error_msg = "Lỗi: Kết nối RAG không khả dụng."
        logger.error(error_msg)
        return {
            "messages": AIMessage(content=error_msg),
            "ai_reply": AIMessage(content=error_msg)
        }

    user_input = state['messages'][-1].content
    chat_history = parsing_messages_to_history(state.get('messages', ''))

    # 1. Retrieval Step
    logger.info("Retrieving context from vector store...")
    context = "Không tìm thấy thông tin liên quan." # Default context
    matches = [] # Default matches
    
    try:
        matches = vector_store.query(
            query_text=user_input,
            topic="tuition_fee",
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
        context = "Lỗi: Không thể truy xuất thông tin học phí."

    # 2. Prompt Formatting Step 
    

    system_prompts = {
        "ROLE": CONST_ASSISTANT_ROLE,
        "SKILLS": CONST_ASSISTANT_SKILLS,
        "TONE": CONST_ASSISTANT_TONE,
        "TASKS": "If the user asks about tuition fees, charges, scholarships, or tuition exemption and reduction policies, provide accurate information from the database.",
        "EXAMPLES": f"""
                        - Học phí ngành Điện tử của Bách Khoa là bao nhiêu?
                        - Chương trình tiên tiến học phí có cao không?
                        - Bách Khoa có học bổng dành cho sinh viên giỏi không?
                        - Có chính sách miễn giảm học phí cho sinh viên khó khăn không?
        """,

        "CONSTRAINTS": f""" 
                        - Assistant's responses MUST be formatted clearly and easy to read (prefer bullet points).
                        - Keep the answers concise and under 200 words.
                        - Use the same language as the user's question.
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
    
    source_info = RAGResponseFormatter.format_sources(matches)

    # 3. Generation 
    try:
        response = completion(
            api_key=os.getenv("GROQ_API_KEY"),
            model=LLM_MODELS['tuition_fee_subgraph']['tuition_fee_node'],
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.3
        )
        final_answer = response.choices[0].message.content
        final_answer = remove_think_tag(final_answer)
    except Exception as e:
        logger.error(f"❌ Error during Groq API call: {e}")
        final_answer = "Xin lỗi, tôi đã gặp lỗi khi tạo câu trả lời."

    # 4. Return 
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