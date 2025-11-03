import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from dotenv import load_dotenv
from logger import logger
from .base_vector_store import BaseVectorStore
from sentence_transformers import CrossEncoder

# --- Imports for Hybrid Search ---
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from .hybrid_helpers import convert_to_pinecone_sparse_vector # The helper file we created

class PineconeStore(BaseVectorStore):
    def __init__(self):
        super().__init__() 
        load_dotenv()
        
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        
        if not self.api_key or not self.index_name:
            raise ValueError("PINECONE_API_KEY or PINECONE_INDEX_NAME not set")
            
        try:
            self.pc = Pinecone(api_key=self.api_key)
            self.index = self.pc.Index(self.index_name)
            logger.info(f"✅ Connected to Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"❌ Error connecting to Pinecone: {e}")
            self.index = None
        
        #  Load all TF-IDF vectorizer models 
        self.vectorizers = {}
        all_topics = ["tuition_fee", "graduate", "regulation_info"] 
        
        for topic in all_topics:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, "tfidf_models", f"{topic}_tfidf.joblib") 
            try:
                self.vectorizers[topic] = joblib.load(path)
                logger.info(f"Loaded TF-IDF model for topic: {topic}")
            except FileNotFoundError:
                logger.warning(f"No TF-IDF model found at {path} for topic: {topic}")
            except Exception as e:
                logger.error(f"Error loading {path}: {e}")
        try:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("✅ Loaded cross-encoder reranking model.")
        except Exception as e:
            logger.error(f"❌ Error loading cross-encoder model: {e}")
            self.reranker = None

    def query(self, 
              query_text: str, 
              topic: str,
              k: int = 3,          
              retrieve_k: int = 25  
             ) -> List[Dict[str, Any]]:
        """
        Query Pinecone with a 2-stage HYBRID + RERANK process.
        1. Retrieve 'retrieve_k' docs using hybrid search (dense + sparse).
        2. Rerank those docs to get the final 'k' best results.
        """
        try:
            if not self.is_healthy():
                raise ConnectionError("Pinecone connection not healthy")
            
            # STAGE 1: HYBRID RETRIEVAL (Broad Search) 
            logger.info(f"Retrieving top {retrieve_k} hybrid docs for topic '{topic}'...")

            # 1a. Create Dense Vector
            dense_vector = self.embedding_model.embed_query(query_text)
            
            # 1b. Create Sparse Vector
            vectorizer = self.vectorizers.get(topic)
            if not vectorizer:
                logger.warning(f"No sparse vectorizer for topic '{topic}', falling back to dense-only search.")
                sparse_vector = {"indices": [], "values": []}
            else:
                query_sparse_matrix = vectorizer.transform([query_text])
                sparse_vector = convert_to_pinecone_sparse_vector(query_sparse_matrix)

            # 1c. Query Pinecone with *both* vectors
            response = self.index.query(
                vector=dense_vector,
                sparse_vector=sparse_vector,
                top_k=retrieve_k, # Retrieve 25 docs
                filter={"topic": topic},
                include_metadata=True
            )
            
            original_matches = response['matches']
            if not original_matches:
                logger.warning(f"No documents found in retrieval phase for topic: {topic}")
                return []
            documents_to_rerank = [match['metadata']['page_content'] for match in original_matches]

            if not documents_to_rerank:
                logger.warning(f"No documents found in retrieval phase for topic: {topic}")
                return []

            # STAGE 2: RERANKING (Precise Re-ordering) 
            logger.info(f"Reranking {len(original_matches)} documents...")
            
            # 2a. Create pairs of [query, document_text]
            pairs = []
            for match in original_matches:
                pairs.append( (query_text, match['metadata']['page_content']) )

            # 2b. Run all pairs through the reranker model
            scores = self.reranker.predict(pairs)
            
            # 2c. Add the new (better) scores back to the original matches
            for i, match in enumerate(original_matches):
                match['rerank_score'] = scores[i]
            
            # 2d. Sort all 25 matches by the new rerank_score
            sorted_matches = sorted(original_matches, key=lambda x: x['rerank_score'], reverse=True)
            
            # 2e. Get the final top 'k' (e.g., 3)
            final_top_k = sorted_matches[:k]

            # STAGE 3: Format Output (Same as before) 
            final_matches = []
            for match in final_top_k:
                final_matches.append({
                    'content': match['metadata']['page_content'],
                    'score': match['rerank_score'], 
                    'metadata': match['metadata']
                })
                    
            return final_matches
            
        except Exception as e:
            logger.error(f"❌ Error querying Pinecone with hybrid rerank: {e}")
            return []
            

            
            
    def is_healthy(self) -> bool:
        """Check if Pinecone connection is working"""
        return self.index is not None