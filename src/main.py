import uvicorn
import traceback
from fastapi import FastAPI, Response, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from genai_agent.agent import build_graph
from langchain_core.messages import HumanMessage
from datetime import datetime
from genai_agent.mongo_db import connect_to_mongo, close_mongo_connection, get_conversations_collection
from motor.motor_asyncio import AsyncIOMotorCollection
from contextlib import asynccontextmanager  

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Xử lý các sự kiện startup và shutdown.
    """
    # --- PHẦN STARTUP ---
    print("Running startup procedures...")
    await connect_to_mongo() # Kết nối đến MongoDB
    
    # Compile graph và lưu nó vào 'app.state'
    # (Cách này tốt hơn là dùng 'global')
    try:
        app.state.agent_graph = build_graph()
        print("✅ LangGraph agent compiled successfully!")
    except Exception as e:
        print(f"❌ Error compiling agent graph: {e}")
        app.state.agent_graph = None
    
    yield # Ứng dụng sẽ chạy tại đây

    # --- PHẦN SHUTDOWN ---
    print("Running shutdown procedures...")
    await close_mongo_connection() # Ngắt kết nối MongoDB


# 1. Initialize the FastAPI app
app = FastAPI(
    title="HCMUT Chatbot Server",
    description="API Server for the LangGraph Chatbot Agent",
    lifespan=lifespan # <-- SỬ DỤNG LIFESPAN MỚI
)
# ===== KẾT THÚC THAY ĐỔI =====


# 2. Add CORS middleware (Giữ nguyên)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Compile agent (Đã XÓA - chuyển vào lifespan)
# global agent_graph = None <-- Dòng này đã bị xóa


# 4. Define the request model (Giữ nguyên)
class ChatRequest(BaseModel):
    message: str
    thread_id: str

# 5. Define the /chat endpoint
# ===== BẮT ĐẦU THAY ĐỔI (Cách lấy agent_graph) =====
@app.post("/chat")
async def chat(
    fastapi_request: Request, # <-- THÊM fastapi_request
    request: ChatRequest,
    collection: AsyncIOMotorCollection = Depends(get_conversations_collection)
):
    """
    Nhận tin nhắn, gọi agent, và lưu lịch sử chat vào MongoDB.
    """
    # Lấy graph từ app.state thay vì dùng global
    agent_graph = fastapi_request.app.state.agent_graph 
    
    if not agent_graph:
        return {"error": "Agent chưa được khởi tạo"}, 500
# ===== KẾT THÚC THAY ĐỔI =====

    # 1. Tạo input cho LangGraph (Giữ nguyên)
    inputs = {
        "messages": [
            HumanMessage(
                content=request.message, 
                additional_kwargs={"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            )
        ]
    }
    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        # 2. Gọi graph.invoke
        response_state = agent_graph.invoke(inputs, config=config)
        ai_reply = response_state.get('ai_reply', None)

        if ai_reply is None:
            ai_content = "Dạ, có vẻ đã xảy ra lỗi. Xin Anh/Chị thử lại."
        else:
            ai_content = ai_reply.content

        # 3. Tạo các document tin nhắn để lưu
        user_message_doc = {
            "sender": "user",
            "content": request.message,
            "timestamp": datetime.now()
        }
        assistant_message_doc = {
            "sender": "assistant",
            "content": ai_content,
            "timestamp": datetime.now()
        }

        # 4. Lưu cả 2 tin nhắn vào MongoDB
        await collection.find_one_and_update(
            {"thread_id": request.thread_id},
            {
                "$push": {
                    "messages": {"$each": [user_message_doc, assistant_message_doc]}
                },
                "$setOnInsert": { 
                    "thread_id": request.thread_id,
                    "created_at": datetime.now()
                }
            },
            upsert=True 
        )

        # 5. Trả về phản hồi của AI
        return {"content": ai_content}

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi gọi agent hoặc MongoDB: {e}")
        traceback.print_exc()
        return {"error": "Lỗi máy chủ khi xử lý yêu cầu"}, 500


# 6. (Optional) A root endpoint for testing (Giữ nguyên)
@app.get("/")
def read_root():
    return {"status": "HCMUT Chatbot API is running"}

# Thêm route cho favicon (Giữ nguyên)
@app.get("/favicon.ico", status_code=204)
async def disable_favicon():
    return Response(content=None)

# 7. Run the server (Giữ nguyên)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)