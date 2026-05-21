"""
ai_services/chatbot.py - Teacher AI Chatbot with RAG support
"""

import uuid
import re
import asyncio
from typing import Optional
from datetime import datetime
import logging

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from database.connection import get_database
from ai_services.gemini_client import get_llm
from vector_store.chroma_client import get_rag_context

logger = logging.getLogger(__name__)

_sessions: dict = {}


def _get_or_create_session(session_id: Optional[str]) -> tuple[str, list]:
    if not session_id or session_id not in _sessions:
        session_id = str(uuid.uuid4())
        _sessions[session_id] = []
    return session_id, _sessions[session_id]


async def chat_with_teacher_bot(
    user_id: str,
    message: str,
    session_id: Optional[str] = None,
    use_rag: bool = True,
) -> dict:
    session_id, history = _get_or_create_session(session_id)

    context = "No documents uploaded yet."
    sources = []
    if use_rag:
        try:
            rag_result = await get_rag_context(user_id, message, n_results=4)
            if rag_result:
                context = rag_result
                sources = re.findall(r"\[Source \d+: (.+?)\]", context)
        except Exception as e:
            logger.warning(f"RAG context fetch failed, continuing without it: {e}")

    system_prompt = f"""You are an intelligent AI teaching assistant designed to help teachers with:
- Answering questions about curriculum and syllabus content
- Generating quizzes, assignments, and activities
- Providing teaching strategies and tips
- Explaining concepts in student-friendly language

CONTEXT FROM UPLOADED DOCUMENTS:
{context}

Always be helpful, professional, and encouraging. Format responses clearly with bullet points when appropriate."""

    messages = [SystemMessage(content=system_prompt)]
    for msg in history[-10:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=message))

    llm = get_llm(temperature=0.7)
    logger.info(f"Chatbot processing message for user {user_id}")

    ai_response = ""
    for attempt in range(3):
        try:
            response = await llm.ainvoke(messages)
            ai_response = response.content
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                wait = 35 * (attempt + 1)
                logger.warning(f"Rate limit hit, retrying in {wait}s...")
                await asyncio.sleep(wait)
            else:
                raise

    if not ai_response:
        raise ValueError("No response received from AI model")

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ai_response})
    _sessions[session_id] = history

    db = get_database()
    await db.chat_history.insert_one({
        "user_id": user_id,
        "session_id": session_id,
        "user_message": message,
        "ai_response": ai_response,
        "sources": sources,
        "created_at": datetime.utcnow(),
    })

    return {"session_id": session_id, "message": ai_response, "sources": sources}


async def get_chat_history(user_id: str, session_id: Optional[str] = None, limit: int = 50) -> list:
    db = get_database()
    query = {"user_id": user_id}
    if session_id:
        query["session_id"] = session_id
    cursor = db.chat_history.find(query, sort=[("created_at", -1)], limit=limit)
    history = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        history.append(doc)
    return list(reversed(history))


async def get_chat_sessions(user_id: str) -> list:
    db = get_database()
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$session_id",
            "last_message": {"$last": "$user_message"},
            "last_activity": {"$max": "$created_at"},
            "message_count": {"$sum": 1},
        }},
        {"$sort": {"last_activity": -1}},
        {"$limit": 20},
    ]
    sessions = []
    async for doc in db.chat_history.aggregate(pipeline):
        sessions.append({
            "session_id": doc["_id"],
            "last_message": doc["last_message"],
            "last_activity": doc["last_activity"],
            "message_count": doc["message_count"],
        })
    return sessions