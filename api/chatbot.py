"""
api/chatbot.py - Teacher AI Chatbot routes
"""

from fastapi import APIRouter, Depends, HTTPException
from models.schemas import ChatRequest, ChatResponse
from auth.jwt_handler import get_current_user
from ai_services.chatbot import chat_with_teacher_bot, get_chat_history, get_chat_sessions

router = APIRouter()


@router.post("/message")
async def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Send a message to the AI teaching assistant.
    
    The chatbot uses RAG to answer questions based on uploaded documents.
    Maintains conversation history within a session.
    """
    try:
        result = await chat_with_teacher_bot(
            user_id=current_user["id"],
            message=request.message,
            session_id=request.session_id,
            use_rag=request.use_rag,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# @router.post("/message")
# async def send_message():
#     print("INSIDE CHAT ROUTE")
#     return {
#         "session_id": "test",
#         "message": "Backend is working",
#         "sources": []
#     }

@router.get("/history")
async def get_history(
    session_id: str = None,
    current_user: dict = Depends(get_current_user),
):
    """Get chat history for the current user (optionally filtered by session)."""
    return await get_chat_history(current_user["id"], session_id)


@router.get("/sessions")
async def list_sessions(current_user: dict = Depends(get_current_user)):
    """Get all chat sessions for the current user."""
    return await get_chat_sessions(current_user["id"])
