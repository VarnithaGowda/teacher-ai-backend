"""
vector_store/chroma_client.py - ChromaDB integration with HuggingFace embeddings

This module handles:
- Initializing ChromaDB persistent client
- Creating/loading collections per user
- Adding document chunks with embeddings
- Querying for relevant context (RAG)
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from typing import List, Dict, Any, Optional
import logging
import os

from config import settings

logger = logging.getLogger(__name__)

# ─── Singleton Embedding Model ────────────────────────────────────
# Load once to avoid reloading on every request (expensive operation)
_embedding_model: Optional[HuggingFaceEmbeddings] = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Return the singleton HuggingFace embedding model.
    Uses sentence-transformers/all-MiniLM-L6-v2 (384 dimensions, fast & accurate).
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _embedding_model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded successfully.")
    return _embedding_model


# ─── ChromaDB Client ──────────────────────────────────────────────
def get_chroma_client() -> chromadb.PersistentClient:
    """Return a persistent ChromaDB client."""
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    return chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


# ─── Collection Name Helper ───────────────────────────────────────
def get_collection_name(user_id: str) -> str:
    """Each user gets their own ChromaDB collection."""
    return f"user_{user_id}_docs"


# ─── Add Documents to Vector Store ───────────────────────────────
async def add_documents_to_vectorstore(
    user_id: str,
    text: str,
    document_id: str,
    filename: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> int:
    """
    Chunk a document and store embeddings in ChromaDB.
    
    Args:
        user_id: Owner of the document
        text: Full document text
        document_id: MongoDB document ID for reference
        filename: Original filename
        chunk_size: Characters per chunk
        chunk_overlap: Overlap between chunks
    
    Returns:
        Number of chunks created
    """
    # Split text into chunks using LangChain's recursive splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)

    if not chunks:
        logger.warning(f"No chunks created for document {document_id}")
        return 0

    # Get embedding model and ChromaDB client
    embeddings = get_embedding_model()
    client = get_chroma_client()
    collection_name = get_collection_name(user_id)

    # Get or create collection
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    # Generate embeddings for all chunks
    chunk_embeddings = embeddings.embed_documents(chunks)

    # Prepare metadata for each chunk
    ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "filename": filename,
            "chunk_index": i,
            "user_id": user_id,
        }
        for i in range(len(chunks))
    ]

    # Add to ChromaDB
    collection.add(
        ids=ids,
        embeddings=chunk_embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    logger.info(f"Added {len(chunks)} chunks for document {document_id}")
    return len(chunks)


# ─── Query Vector Store ───────────────────────────────────────────
async def query_vectorstore(
    user_id: str,
    query: str,
    n_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieve the most relevant document chunks for a query.
    
    Args:
        user_id: User whose documents to search
        query: The search query
        n_results: Number of results to return
    
    Returns:
        List of dicts with 'text', 'filename', 'score'
    """
    embeddings = get_embedding_model()
    client = get_chroma_client()
    collection_name = get_collection_name(user_id)

    # Check if collection exists
    existing = [c.name for c in client.list_collections()]
    if collection_name not in existing:
        logger.info(f"No documents found for user {user_id}")
        return []

    collection = client.get_collection(collection_name)

    # Check if collection has documents
    if collection.count() == 0:
        return []

    # Embed the query
    query_embedding = embeddings.embed_query(query)

    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    # Format results
    formatted = []
    for i, doc in enumerate(results["documents"][0]):
        formatted.append({
            "text": doc,
            "filename": results["metadatas"][0][i].get("filename", "Unknown"),
            "document_id": results["metadatas"][0][i].get("document_id", ""),
            "score": 1 - results["distances"][0][i],  # Convert distance to similarity
        })

    return formatted


# ─── Delete User Documents ────────────────────────────────────────
async def delete_document_from_vectorstore(user_id: str, document_id: str):
    """Remove all chunks of a specific document from ChromaDB."""
    client = get_chroma_client()
    collection_name = get_collection_name(user_id)

    existing = [c.name for c in client.list_collections()]
    if collection_name not in existing:
        return

    collection = client.get_collection(collection_name)
    # Delete by metadata filter
    collection.delete(where={"document_id": document_id})
    logger.info(f"Deleted document {document_id} from vector store")


# ─── Get Context String for RAG ───────────────────────────────────
async def get_rag_context(user_id: str, query: str, n_results: int = 4) -> str:
    """
    Get formatted context string from relevant documents for RAG.
    
    Returns:
        Formatted string with relevant chunks and their sources
    """
    results = await query_vectorstore(user_id, query, n_results)

    if not results:
        return "No relevant documents found in your uploaded materials."

    context_parts = []
    for i, result in enumerate(results, 1):
        context_parts.append(
            f"[Source {i}: {result['filename']}]\n{result['text']}"
        )

    return "\n\n---\n\n".join(context_parts)
