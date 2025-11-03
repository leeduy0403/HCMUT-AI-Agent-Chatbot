import scipy.sparse
from typing import Optional # <--- ADD THIS

def convert_to_pinecone_sparse_vector(v: scipy.sparse.csr_matrix) -> Optional[dict]:
    """
    Converts a SciPy sparse matrix (from TF-IDF) into the
    dictionary format required by Pinecone for sparse vectors.
    Returns None if the vector is empty.
    """
    if v.nnz == 0:
        return None  # 
    
    # Get the non-zero indices and their values
    indices = v.indices.tolist()
    values = v.data.tolist()
    
    return {"indices": indices, "values": values}