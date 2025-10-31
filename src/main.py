import uvicorn
import traceback
from fastapi import FastAPI, Response, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi.encoders import jsonable_encoder
from genai_agent.agent import build_graph
from genai_agent.mongo_db import connect_to_mongo, close_mongo_connection, get_collection
from motor.motor_asyncio import AsyncIOMotorCollection
from langchain_core.messages import HumanMessage

class RenameRequest(BaseModel):
    new_title: str

class ChatRequest(BaseModel):
    message: str
    thread_id: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Running startup procedures...")
    await connect_to_mongo()
    try:
        app.state.agent_graph = build_graph()
        print("✅ LangGraph agent compiled successfully!")
    except Exception as e:
        print(f"❌ Error compiling agent graph: {e}")
        app.state.agent_graph = None
    yield
    print("Running shutdown procedures...")
    await close_mongo_connection()

app = FastAPI(
    title="HCMUT Chatbot Server",
    description="API Server for the LangGraph Chatbot Agent",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# Dependency helper for type hints (keeps using your get_collection implementation)
def conv_collection() -> AsyncIOMotorCollection:
    return get_collection("conversations")

# GET /history - trả về danh sách các conversation (thread_id, title, created_at)
@app.get("/history")
async def get_history(collection: AsyncIOMotorCollection = Depends(lambda: conv_collection())):
    history = await collection.find({}, {"thread_id": 1, "title": 1, "created_at": 1, "_id": 0})\
                              .sort("created_at", -1).to_list(length=100)
    return jsonable_encoder(history)

# GET /history/{thread_id} - trả về toàn bộ conversation (kèm messages)
@app.get("/history/{thread_id}")
async def get_conversation_messages(
    thread_id: str,
    collection: AsyncIOMotorCollection = Depends(lambda: conv_collection())
):
    conversation = await collection.find_one({"thread_id": thread_id}, {"_id": 0})
    return jsonable_encoder(conversation) if conversation else {}

# PUT /history/{thread_id}/rename - đổi tên conversation
@app.put("/history/{thread_id}/rename")
async def rename_conversation(
    thread_id: str,
    request: RenameRequest,
    collection: AsyncIOMotorCollection = Depends(lambda: conv_collection())
):
    if not request.new_title or request.new_title.strip() == "":
        raise HTTPException(status_code=400, detail="Title không hợp lệ.")
    result = await collection.update_one(
        {"thread_id": thread_id},
        {"$set": {"title": request.new_title}}
    )
    if result.modified_count == 1:
        return {"status": "success", "message": "Title updated."}
    # Có thể cập nhật không đổi nếu title giống trước đó
    existing = await collection.find_one({"thread_id": thread_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"status": "ok", "message": "Title unchanged."}

# DELETE /history/{thread_id} - xóa conversation
@app.delete("/history/{thread_id}")
async def delete_conversation(
    thread_id: str,
    collection: AsyncIOMotorCollection = Depends(lambda: conv_collection())
):
    result = await collection.delete_one({"thread_id": thread_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại.")
    return {"status": "success", "message": "Conversation deleted."}

# POST /chat - gửi message, lưu message vào conversation (create nếu chưa có)
@app.post("/chat")
async def chat(
    fastapi_request: Request,
    request: ChatRequest,
    collection: AsyncIOMotorCollection = Depends(lambda: conv_collection())
):
    agent_graph = fastapi_request.app.state.agent_graph
    if not agent_graph:
        raise HTTPException(status_code=500, detail="Agent chưa được khởi tạo")

    # Prepare input for agent (adjust per your agent API)
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
        # If your agent_graph.invoke is async, await it. The original code used synchronous invoke.
        response_state = agent_graph.invoke(inputs, config=config)
        ai_reply = response_state.get('ai_reply', None)
        ai_content = ai_reply.content if ai_reply else "Dạ, có vẻ đã xảy ra lỗi. Xin Anh/Chị thử lại."

        # Prepare message docs
        now = datetime.now()
        user_message_doc = {"sender": "user", "content": request.message, "timestamp": now}
        assistant_message_doc = {"sender": "assistant", "content": ai_content, "timestamp": now}

        # Ensure conversation exists; if not, create with a default title (first 5 words)
        existing_convo = await collection.find_one({"thread_id": request.thread_id}, {"title": 1})
        if not existing_convo:
            default_title = " ".join(request.message.split()[:5]) or "Cuộc trò chuyện mới"
            # Create a new document
            doc = {
                "thread_id": request.thread_id,
                "title": default_title,
                "created_at": now,
                "messages": [user_message_doc, assistant_message_doc]
            }
            await collection.insert_one(doc)
        else:
            # Append messages to existing conversation
            await collection.update_one(
                {"thread_id": request.thread_id},
                {"$push": {"messages": {"$each": [user_message_doc, assistant_message_doc]}}}
            )

        return {
        "content": ai_content,
        "thread_id": request.thread_id,
        "title": existing_convo["title"] if existing_convo and "title" in existing_convo 
                else " ".join(request.message.split()[:5]) or "Cuộc trò chuyện mới",
        "created_at": datetime.now().isoformat()
    }

    except Exception as e:
        print(f"Lỗi nghiêm trọng: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Lỗi máy chủ")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
