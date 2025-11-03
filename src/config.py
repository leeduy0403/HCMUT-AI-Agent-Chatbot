import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

APP_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LLM_MODELS = {
    "router": {
        "router_node": os.getenv('GROQ_LLM_MODEL_LLAMA_70B')
    },
    "greeting_subgraph": {
        "greeting_node": os.getenv('GROQ_LLM_MODEL_LLAMA_70B')
    },
    "off_topic_subgraph": {
        "off_topic_node": os.getenv('GROQ_LLM_MODEL_LLAMA_70B')
    },
    "llm_subgraph": {
        "llm_node": os.getenv('OPEN_LLM_MODEL_GPT_4')
    },
    "tuition_fee_subgraph": {
        "tuition_fee_node": os.getenv('GROQ_LLM_MODEL_LLAMA_70B')
    },
    "regulation_info_subgraph": {
        "regulation_info_node": os.getenv('GROQ_LLM_MODEL_LLAMA_70B')
    },
    "graduate_subgraph":{
        "graduate_node": os.getenv('GROQ_LLM_MODEL_LLAMA_70B')
    },
}