import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from tqdm import tqdm

from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv, find_dotenv

# Configuration
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
EMBEDDING_BATCH_SIZE = 50
UPLOAD_BATCH_SIZE = 100
VECTOR_DIMENSION = 384  # for all-MiniLM-L6-v2

load_dotenv(find_dotenv())

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


# --- 2. Define your data "topics" and their paths ---
TOPIC_PATHS = {
    "all": "D:/HCMUT-AI-Agent-Chatbot/BKU_KB/BKU_KB"
}    #"uni_info": "D:\HCMUT-AI-Agent-Chatbot\BKU_KB\BKU_KB\uni_info", 
    #"graduate": "D:\HCMUT-AI-Agent-Chatbot\BKU_KB\BKU_KB\graduate",
    #"undergraduate": "D:\HCMUT-AI-Agent-Chatbot\BKU_KB\BKU_KB\undergraduate",


# --- 3. Pinecone Client ---
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    # Check if index exists, if not create it
    if index_name not in [index.name for index in pc.list_indexes()]:
        print(f"Index '{index_name}' not found. Creating a new serverless index...")
        pc.create_index(
            name=index_name,
            dimension=384,  # dimension for all-MiniLM-L6-v2
            metric="cosine",
            
            # --- THIS IS THE FIX ---
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
            # --- END OF FIX ---
        )
        print(f"Created new Pinecone index: {index_name}")
    else:
        print(f"Index '{index_name}' already exists. Connecting.")
    
    pinecone_index = pc.Index(index_name)
except Exception as e:
    raise Exception(f"Failed to initialize Pinecone: {str(e)}")

# --- 4. A Reusable Upload Function (with metadata) ---
def upload_topic(topic_tag: str, doc_path: str):
    try:
        print(f"\n--- Processing topic: {topic_tag} ---")
        
        if not os.path.exists(doc_path):
            print(f"Directory not found: {doc_path}")
            return
        
        # 1. Load docs with proper error handling for different file types
        supported_files = {
            "*.pdf": PyPDFLoader,
            "*.docx": UnstructuredWordDocumentLoader,
            # Add more file types as needed
        }
        
        documents = []
        for glob_pattern, loader_cls in supported_files.items():
            try:
                loader = DirectoryLoader(doc_path, glob=glob_pattern, loader_cls=loader_cls)
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                print(f"Warning: Error loading {glob_pattern} files: {str(e)}")
        
        if not documents:
            print(f"No supported documents found in {doc_path}. Skipping.")
            return

        # 2. Add metadata *before* splitting
        for doc in documents:
            doc.metadata.update({
                "topic": topic_tag,
                "source": os.path.basename(doc.metadata.get("source", "")),
                "created_at": str(datetime.now()),
            })
        
        # 3. Split docs with error handling
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=512,
                chunk_overlap=50,
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ";"]
            )
            chunks = text_splitter.split_documents(documents)
            print(f"Found {len(documents)} docs, split into {len(chunks)} chunks.")
        except Exception as e:
            print(f"Error splitting documents: {str(e)}")
            return

        # 4. Embed chunks in batches
        print("Embedding document chunks...")
        batch_size = 50  # Smaller batch size for embeddings
        vectors = []
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.page_content for chunk in batch]
            try:
                batch_vectors = EMBEDDING_MODEL.embed_documents(texts)
                vectors.extend(batch_vectors)
                print(f"Embedded batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
            except Exception as e:
                print(f"Error embedding batch {i//batch_size + 1}: {str(e)}")
                continue
                
        if not vectors:
            print("No vectors generated. Skipping upload.")
            return
            
        print("Embedding complete.")

    # 5. Prepare vectors for manual upsert
        vectors_to_upsert = []
        for i, chunk in enumerate(chunks):
            if i >= len(vectors): # Fix for batches that failed
                break
        # Create a unique ID to prevent duplicates
            vector_id = f"{topic_tag}-{uuid.uuid4()}" 
        
        # Store the text content IN the metadata
            metadata = chunk.metadata
            metadata['page_content'] = chunk.page_content
        
            vectors_to_upsert.append({
                "id": vector_id,
                "values": vectors[i],
                "metadata": metadata
        })

    # 6. Upload to Pinecone in batches
        print(f"Uploading {len(vectors_to_upsert)} vectors to Pinecone...")
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            pinecone_index.upsert(vectors=batch)
        
        print(f"✅ Successfully uploaded '{topic_tag}' chunks.")
    except Exception as e:
        print(f"❌ An unexpected error occurred while processing topic '{topic_tag}': {str(e)}")
# --- 5. Main function to run all uploads ---
if __name__ == "__main__":
    for topic_tag, doc_path in TOPIC_PATHS.items():
        upload_topic(topic_tag, doc_path)
    
    print("\nAll data uploads to master index complete.")