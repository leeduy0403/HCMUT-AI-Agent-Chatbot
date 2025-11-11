import uvicorn
import traceback
import io
from fastapi import FastAPI, Response, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi.encoders import jsonable_encoder
from genai_agent.agent import build_graph
from genai_agent.mongo_db import connect_to_mongo, close_mongo_connection, get_collection
from motor.motor_asyncio import AsyncIOMotorCollection
from langchain_core.messages import HumanMessage
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class RenameRequest(BaseModel):
    new_title: str

class ChatRequest(BaseModel):
    message: str
    thread_id: str

class SpeakRequest(BaseModel):
    text: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Running startup procedures...")
    await connect_to_mongo()
    app.state.openai_client = AsyncOpenAI()
    try:
        app.state.agent_graph = build_graph()
        print("✅ LangGraph agent compiled successfully!")
    except Exception as e:
        print(f"❌ Error compiling agent graph: {e}")
        app.state.agent_graph = None
    yield
    print("Running shutdown procedures...")
    await close_mongo_connection()
    await app.state.openai_client.close()

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
async def get_history(
    collection: AsyncIOMotorCollection = Depends(lambda: get_collection("conversations"))
):
    """
    Sử dụng Aggregation Pipeline để sắp xếp một cách mạnh mẽ.
    Nó sẽ sắp xếp theo 'updated_at' nếu có, nếu không sẽ dùng 'created_at'.
    """
    pipeline = [
        {
            "$project": {
                "thread_id": 1,
                "title": 1,
                "_id": 0,
                "last_active_time": {
                    "$ifNull": ["$updated_at", "$created_at"]
                }
            }
        },
        {
            "$sort": {"last_active_time": -1}
        }
    ]
    
    history_cursor = collection.aggregate(pipeline)
    history = await history_cursor.to_list(length=None)
    
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
    collection: AsyncIOMotorCollection = Depends(lambda: get_collection("conversations"))
):
    agent_graph = fastapi_request.app.state.agent_graph
    if not agent_graph:
        return {"error": "Agent chưa được khởi tạo"}, 500

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
        response_state = agent_graph.invoke(inputs, config=config)
        ai_reply = response_state.get('ai_reply', None)
        ai_content = ai_reply.content if ai_reply else "Dạ, có vẻ đã xảy ra lỗi. Xin Anh/Chị thử lại."

        user_message_doc = {"sender": "user", "content": request.message, "timestamp": datetime.now()}
        assistant_message_doc = {"sender": "assistant", "content": ai_content, "timestamp": datetime.now()}

        existing_convo = await collection.find_one({"thread_id": request.thread_id}, {"title": 1})
        
        # Bắt đầu tài liệu cập nhật (update_doc)
        update_doc = {
            "$push": {"messages": {"$each": [user_message_doc, assistant_message_doc]}},
            # $set: Cập nhật 'updated_at' mỗi khi có tin nhắn mới
            "$set": {"updated_at": datetime.now()},
            # $setOnInsert: Chỉ đặt các giá trị này khi tạo mới
            "$setOnInsert": {"thread_id": request.thread_id, "created_at": datetime.now()}
        }
        
        # Nếu chưa có title (tin nhắn đầu tiên), thêm 'title' vào $set
        if not existing_convo or "title" not in existing_convo:
            default_title = " ".join(request.message.split()[:5])
            update_doc["$set"]["title"] = default_title

        await collection.find_one_and_update(
            {"thread_id": request.thread_id}, update_doc, upsert=True
        )

        return {"content": ai_content}

    except Exception as e:
        print(f"Lỗi nghiêm trọng: {e}")
        traceback.print_exc()
        return {"error": "Lỗi máy chủ"}, 500

@app.post("/speak")
async def speak(
    fastapi_request: Request,
    request: SpeakRequest
):
    """
    Nhận văn bản và trả về file âm thanh MP3 từ OpenAI.
    """
    try:
        client = fastapi_request.app.state.openai_client
        
        # Gọi API OpenAI TTS
        # Model 'tts-1' tự động nhận diện ngôn ngữ
        response = await client.audio.speech.create(
            model="tts-1",
            voice="alloy", # (alloy, echo, fable, onyx, nova, shimmer)
            input=request.text,
            response_format="mp3"
        )

        # Stream file MP3 về trình duyệt
        return StreamingResponse(io.BytesIO(response.content), media_type="audio/mpeg")

    except Exception as e:
        print(f"Lỗi khi tạo audio: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Không thể tạo file âm thanh.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
