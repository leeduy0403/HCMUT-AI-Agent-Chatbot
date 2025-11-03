import motor.motor_asyncio
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

MONGO_CONNECTION_STRING = os.getenv("MONGO_DB_CONNECTION_STRING")

DATABASE_NAME = "hcmut_chatbot_db"

class MongoDB:
    client: motor.motor_asyncio.AsyncIOMotorClient = None
    db: motor.motor_asyncio.AsyncIOMotorDatabase = None

db = MongoDB()

async def connect_to_mongo():
    """Kết nối đến MongoDB Atlas khi server FastAPI khởi động."""
    print("Connecting to MongoDB Atlas...")
    try:
        db.client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)
        db.db = db.client[DATABASE_NAME]
        await db.client.admin.command('ping') # Kiểm tra kết nối
        print("✅ Connected to MongoDB successfully!")
    except Exception as e:
        print(f"❌ Could not connect to MongoDB: {e}")

async def close_mongo_connection():
    """Đóng kết nối MongoDB khi server FastAPI tắt."""
    print("Closing MongoDB connection...")
    db.client.close()
    print("✅ MongoDB connection closed.")

def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Dependency để lấy instance của database."""
    if db.db is None:
        raise Exception("Database is not initialized. Call connect_to_mongo first.")
    return db.db

def get_collection(name: str) -> motor.motor_asyncio.AsyncIOMotorCollection:
    db_instance = get_database()
    return db_instance[name]