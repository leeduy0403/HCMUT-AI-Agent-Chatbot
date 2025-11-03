from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from langchain_huggingface import HuggingFaceEmbeddings

class BaseVectorStore(ABC):
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    @abstractmethod
    def query(self, 
             query_text: str, 
             topic: str, 
             k: int = 3) -> List[Dict[str, Any]]:
        """Query the vector store"""
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if vector store connection is healthy"""
        pass