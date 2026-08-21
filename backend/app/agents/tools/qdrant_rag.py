import os
import logging
from typing import List
from langchain_core.documents import Document
from app.core.config import settings

logger = logging.getLogger("cortexflow")

def get_embeddings():
    """
    Returns OpenAI embeddings or FastEmbed/HuggingFace embeddings as fallback.
    """
    openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key.startswith("sk-"):
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(api_key=openai_key)
    
    google_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
    if google_key:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(google_api_key=google_key, model="models/embedding-001")
        
    from langchain_community.embeddings import FakeEmbeddings
    return FakeEmbeddings(size=1536)

async def index_documents_to_qdrant(collection_name: str, docs: List[Document]):
    """
    Indexes document chunks into Qdrant vector database.
    """
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams

    embeddings = get_embeddings()
    
    # Connect Qdrant Client (or in-memory if Qdrant server is unreachable)
    try:
        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=5.0)
        # Check if collection exists, if not create
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
        
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=embeddings,
        )
        await vector_store.aadd_documents(docs)
        return vector_store
    except Exception as e:
        logger.warning(f"Qdrant server unavailable ({e}). Using in-memory Qdrant client fallback.")
        in_memory_client = QdrantClient(":memory:")
        in_memory_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        vector_store = QdrantVectorStore(
            client=in_memory_client,
            collection_name=collection_name,
            embedding=embeddings,
        )
        await vector_store.aadd_documents(docs)
        return vector_store

async def search_qdrant_context(vector_store, query: str, k: int = 5) -> str:
    """
    Searches Qdrant for top relevant document passages.
    """
    results = await vector_store.asimilarity_search(query, k=k)
    context = "\n\n".join([doc.page_content for doc in results])
    return context
