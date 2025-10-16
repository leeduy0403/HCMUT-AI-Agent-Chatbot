import os
from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv())

APP_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LLM_MODELS = {
    
}