"""
ai_services/rag_pipeline.py - RAG Document Processing Pipeline

Handles document upload, parsing, chunking, and embedding storage.
"""

import os
import uuid
from datetime import datetime
from typing import Optional
import logging

from database.connection import get_database
from vector_store.chroma_client import add_documents_to_vectorstore, delete_document_from_vectorstore
from utils.file_parser import parse_pdf, parse_docx, parse_text_file

logger = logging.getLogger(__name__)


async def process_and_store_document(
    user_id: str,
    file_path: str,
    filename: str,
    file_type: str,
) -> dict:
    """
    Full RAG pipeline: parse → chunk → embed → store.
    
    Args:
        user_id: Owner of the document
        file_path: Path to the uploaded file
        filename: Original filename
        file_type: 'pdf', 'docx', or 'txt'
    
    Returns:
        Dict with document_id and chunks_created
    """
    # Step 1: Parse the document to extract text
    logger.info(f"Parsing document: {filename} ({file_type})")
    
    if file_type == "pdf":
        text = parse_pdf(file_path)
    elif file_type == "docx":
        text = parse_docx(file_path)
    elif file_type in ("txt", "text"):
        text = parse_text_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    if not text or len(text.strip()) < 50:
        raise ValueError("Document appears to be empty or unreadable")

    # Step 2: Save document metadata to MongoDB
    db = get_database()
    document_id = str(uuid.uuid4())
    doc = {
        "document_id": document_id,
        "user_id": user_id,
        "filename": filename,
        "file_type": file_type,
        "file_path": file_path,
        "text_length": len(text),
        "status": "processing",
        "created_at": datetime.utcnow(),
    }
    await db.documents.insert_one(doc)

    # Step 3: Chunk and embed into ChromaDB
    logger.info(f"Chunking and embedding document: {document_id}")
    chunks_created = await add_documents_to_vectorstore(
        user_id=user_id,
        text=text,
        document_id=document_id,
        filename=filename,
    )

    # Step 4: Update status in MongoDB
    await db.documents.update_one(
        {"document_id": document_id},
        {"$set": {"status": "ready", "chunks_created": chunks_created}},
    )

    logger.info(f"Document {document_id} processed: {chunks_created} chunks")
    return {
        "document_id": document_id,
        "filename": filename,
        "chunks_created": chunks_created,
        "message": f"Document processed successfully with {chunks_created} chunks",
    }


async def get_user_documents(user_id: str) -> list:
    """Get all documents uploaded by a user."""
    db = get_database()
    cursor = db.documents.find(
        {"user_id": user_id},
        sort=[("created_at", -1)],
    )
    docs = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        # Don't expose file paths
        doc.pop("file_path", None)
        docs.append(doc)
    return docs


async def delete_document(user_id: str, document_id: str) -> bool:
    """Delete a document from MongoDB and ChromaDB."""
    db = get_database()
    
    # Get document info
    doc = await db.documents.find_one({"document_id": document_id, "user_id": user_id})
    if not doc:
        return False

    # Delete file from disk
    file_path = doc.get("file_path")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    # Delete from ChromaDB
    await delete_document_from_vectorstore(user_id, document_id)

    # Delete from MongoDB
    await db.documents.delete_one({"document_id": document_id, "user_id": user_id})

    logger.info(f"Deleted document {document_id}")
    return True
