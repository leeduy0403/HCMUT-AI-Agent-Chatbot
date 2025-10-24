import os
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from litellm import completion
from langchain_core.messages import AIMessage
from logger import logger
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from ...states.agent_state import AgentState
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

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

load_dotenv(find_dotenv())

# --- Load your database documents ---
def load_tfidf_db(vector_db_path="C://Users//Admin//OneDrive//Sales-AI-Agent//vectorstores//tuition_db_faiss"):
    """
    This assumes you have stored documents in the FAISS folder previously.
    Instead of embeddings, we only need the text data.
    You can adjust this to directly load plain text documents.
    """

    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.load_local(vector_db_path, embedding_model, allow_dangerous_deserialization=True)

    # Extract all text content
    docs = [doc.page_content for doc in db.docstore._dict.values()]

    # Build TF-IDF model
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(docs)
    return vectorizer, tfidf_matrix, docs


# --- TF-IDF retrieval function ---
def retrieve_context_tfidf(vectorizer, tfidf_matrix, documents, query, k=3):
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = scores.argsort()[::-1][:k]
    context_text = "\n\n".join([documents[i] for i in top_indices])
    return context_text


# --- Tuition Fee Node (main logic) ---
def tuition_fee_node(state: AgentState):
    logger.info("tuition_fee_node called.")
    user_input = state['messages'][-1].content
    chat_history = parsing_messages_to_history(state.get('messages', ''))

    # Load TF-IDF database
    vectorizer, tfidf_matrix, docs = load_tfidf_db()
    context = retrieve_context_tfidf(vectorizer, tfidf_matrix, docs, user_input, k=3)
    print("Retrieved Context:", context)

    # Combine with system prompt
    final_prompt = f"""
    # Role
    {CONST_ASSISTANT_ROLE}

    # Skills
    {CONST_ASSISTANT_SKILLS}

    # Tone
    {CONST_ASSISTANT_TONE}

    # Tasks
    If the user asks about tuition fees, charges, scholarships, or tuition exemption and reduction policies, provide accurate information from the database.

    # Examples
    - Học phí ngành Điện tử của Bách Khoa là bao nhiêu?
    - Chương trình tiên tiến học phí có cao không?
    - Bách Khoa có học bổng dành cho sinh viên giỏi không?
    - Có chính sách miễn giảm học phí cho sinh viên khó khăn không?

    # Constraints
    - Assistant's responses MUST be formatted clearly and easy to read (prefer bullet points).
    - Keep the answers concise and under 200 words.
    - Use the same language as the user's question.
    {CONST_FORM_ADDRESS_IN_VN}

    # Important Information
    - 1 academic year = 2 semesters (1 năm học = 2 học kỳ).
    - Pay attention to the abbreviations that have been explained in the document to better understand the user input.

    # Chat History:
    {chat_history}

    # Tuition Info from DB:
    {context}

    User’s question: {user_input}
    Answer:
    """

    # Call the model for final answer
    response = completion(
        api_key=os.getenv("GROQ_API_KEY"),
        model=LLM_MODELS['tuition_fee_subgraph']['tuition_fee_node'],
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0.7
    )

    ai_message = AIMessage(
        content=remove_think_tag(response.choices[0].message.content),
        additional_kwargs={"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    )

    return {
        "messages": ai_message,
        "ai_reply": ai_message
    }
