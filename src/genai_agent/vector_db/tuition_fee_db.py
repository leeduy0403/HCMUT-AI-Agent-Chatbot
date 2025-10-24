import os
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Khai bao bien
pdf_data_path = "C://Users//Admin//OneDrive//AESS//BKU_KB//tuition fee"
vector_db_path = "vectorstores/tuition_db_faiss"

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"


def create_db_from_files():
    # Khai bao loader de quet toan bo thu muc dataa
    loader = DirectoryLoader(pdf_data_path, glob="*.pdf", loader_cls = PyPDFLoader)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"Number of chunks: {len(chunks)}")

    # Embeding
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(chunks, embedding_model)
    db.save_local(vector_db_path)
    return db



create_db_from_files()