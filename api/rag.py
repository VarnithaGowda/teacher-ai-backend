"""
api/rag.py - Document upload and RAG management routes
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from auth.jwt_handler import get_current_user
from ai_services.rag_pipeline import process_and_store_document, get_user_documents, delete_document
from utils.file_parser import get_file_type
from utils.helpers import save_upload_file

router = APIRouter()


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a document (PDF, DOCX, TXT) to the RAG knowledge base.
    
    The document will be:
    1. Parsed to extract text
    2. Split into chunks using LangChain text splitter
    3. Embedded using HuggingFace sentence-transformers
    4. Stored in ChromaDB for retrieval
    
    The chatbot will use these documents to answer questions.
    """
    # Validate file type
    try:
        file_type = get_file_type(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save file to disk
    file_path, filename = await save_upload_file(file, current_user["id"])

    # Process through RAG pipeline
    try:
        result = await process_and_store_document(
            user_id=current_user["id"],
            file_path=file_path,
            filename=filename,
            file_type=file_type,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.get("/documents")
async def list_documents(current_user: dict = Depends(get_current_user)):
    """List all documents uploaded by the current teacher."""
    return await get_user_documents(current_user["id"])


@router.delete("/documents/{document_id}")
async def remove_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a document from the knowledge base."""
    success = await delete_document(current_user["id"], document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}
