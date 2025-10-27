import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from genai_agent.agent import build_graph  # Import your graph builder
from langchain_core.messages import HumanMessage  # <-- THÊM DÒNG NÀY
from datetime import datetime

# 1. Initialize the FastAPI app
app = FastAPI(
    title="HCMUT Chatbot Server",
    description="API Server for the LangGraph Chatbot Agent",
)

# 2. Add CORS middleware
# This allows your frontend (running on a different domain) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# 3. Compile your LangGraph agent
# This loads the agent into memory when the server starts
try:
    agent_graph = build_graph()
    print("✅ LangGraph agent compiled successfully!")
except Exception as e:
    print(f"❌ Error compiling agent graph: {e}")
    agent_graph = None

# 4. Define the request model
# This ensures the data from the frontend has the correct shape
class ChatRequest(BaseModel):
    message: str
    thread_id: str  # To maintain conversation memory

# 5. Define the /chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Nhận tin nhắn của người dùng và thread_id, trả về phản hồi của agent.
    """
    if not agent_graph:
        return {"error": "Agent chưa được khởi tạo"}, 500

    # 1. Tạo input GIỐNG HỆT như trong console.py
    inputs = {
        "messages": [
            HumanMessage(
                content=request.message, 
                additional_kwargs={"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            )
        ]
    }
    
    # 2. Tạo config (giống như bạn đã làm)
    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        # 3. Gọi graph.invoke
        response_state = agent_graph.invoke(inputs, config=config)
        
        # 4. Lấy câu trả lời bằng logic CHÍNH XÁC từ console.py
        ai_reply = response_state.get('ai_reply', None)

        if ai_reply is None:
            # Trường hợp agent chạy xong nhưng không có tin nhắn trả lời
            print("Cảnh báo: 'ai_reply' là None. Kiểm tra lại các node trong graph.")
            return {"content": "Dạ, có vẻ đã xảy ra lỗi. Xin Anh/Chị thử lại."}
        else:
            # Gửi nội dung tin nhắn về cho frontend
            return {"content": ai_reply.content}

    except Exception as e:
        # Nếu có lỗi, in ra terminal để debug
        print(f"Lỗi nghiêm trọng khi gọi agent: {e}")
        import traceback
        traceback.print_exc()
        return {"error": "Lỗi máy chủ khi xử lý yêu cầu"}, 500

# 6. (Optional) A root endpoint for testing
@app.get("/")
def read_root():
    return {"status": "HCMUT Chatbot API is running"}

# 7. Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)