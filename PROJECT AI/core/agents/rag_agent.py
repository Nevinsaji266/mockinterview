import os
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from .config import get_embeddings

def recursive_split_text(text, chunk_size=500, chunk_overlap=100, separators=None):
    """
    Custom implementation of recursive character text splitter to bypass LangChain version changes.
    """
    if separators is None:
        separators = ["\n\n", "\n", " ", ""]
        
    if len(text) <= chunk_size:
        return [text]
        
    separator = separators[0]
    for sep in separators:
        if sep in text:
            separator = sep
            break
            
    splits = text.split(separator)
    chunks = []
    current_chunk = ""
    
    for split in splits:
        if len(current_chunk) + len(split) + len(separator) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            if len(split) > chunk_size:
                remaining_seps = [s for s in separators if s != separator] or [""]
                chunks.extend(recursive_split_text(split, chunk_size, chunk_overlap, remaining_seps))
                current_chunk = ""
            else:
                overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                current_chunk = overlap_text + separator + split
        else:
            if current_chunk:
                current_chunk += separator + split
            else:
                current_chunk = split
                
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def get_faiss_index_path(user_id):
    """
    Determines the path where the user's FAISS index is saved.
    """
    # Use media root if Django settings are configured, otherwise relative directory
    try:
        from django.conf import settings
        base_dir = os.path.join(settings.MEDIA_ROOT, "faiss_indexes")
    except Exception:
        base_dir = os.path.join("media", "faiss_indexes")
    
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, f"user_{user_id}")

def build_rag_index(user_id, resume_text):
    """
    Splits the resume text, generates embeddings, and saves it in a local FAISS index.
    """
    if not resume_text:
        return False
        
    # 1. Chunking
    chunks = recursive_split_text(resume_text, chunk_size=500, chunk_overlap=100)
    docs = [Document(page_content=chunk) for chunk in chunks]
    
    # 2. Embeddings and FAISS indexing
    embeddings = get_embeddings()
    db = FAISS.from_documents(docs, embeddings)
    
    # 3. Store FAISS database locally
    index_path = get_faiss_index_path(user_id)
    db.save_local(index_path)
    return True

def retrieve_context(user_id, query, k=3):
    """
    Loads the FAISS index for the user and retrieves the top-k relevant chunks.
    """
    index_path = get_faiss_index_path(user_id)
    
    # Check if index exists
    if not os.path.exists(os.path.join(index_path, "index.faiss")):
        return ""
        
    try:
        embeddings = get_embeddings()
        db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        docs = db.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        print(f"Error retrieving context from FAISS: {e}")
        return ""
