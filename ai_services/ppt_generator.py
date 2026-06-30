"""
ai_services/ppt_generator.py
AI PowerPoint Presentation Generation Service
"""

from typing import List
from datetime import datetime
from bson import ObjectId
import logging

from database.connection import get_database
from prompts.ppt_prompt import ppt_prompt
from ai_services.gemini_client import get_llm

logger = logging.getLogger(__name__)


async def generate_presentation(
    user_id: str,
    subject: str,
    grade_level: str,
    difficulty: str,
    presentation_style: str,
    audience: str,
    slides: int,
    topics: List[str],
    instructions: str,
) -> dict:
    """
    Generate AI Presentation using Gemini.
    """

    topics_text = "\n".join(f"- {topic}" for topic in topics)

    formatted_prompt = ppt_prompt.format(
        subject=subject,
        grade_level=grade_level,
        presentation_style=presentation_style,
        audience=audience,
        difficulty=difficulty,
        slides=slides,
        topics=topics_text,
        instructions=instructions,
    )

    llm = get_llm(temperature=0.6)

    logger.info(
        f"Generating Presentation for {subject} ({grade_level})"
    )

    response = await llm.ainvoke(formatted_prompt)

    presentation = response.content

    db = get_database()

    doc = {
        "user_id": user_id,
        "subject": subject,
        "grade_level": grade_level,
        "difficulty": difficulty,
        "presentation_style": presentation_style,
        "audience": audience,
        "slides": slides,
        "topics": topics,
        "instructions": instructions,
        "presentation": presentation,
        "created_at": datetime.utcnow(),
    }

    result = await db.presentations.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "subject": subject,
        "grade_level": grade_level,
        "difficulty": difficulty,
        "presentation_style": presentation_style,
        "audience": audience,
        "slides": slides,
        "presentation": presentation,
        "created_at": doc["created_at"],
    }


async def get_presentations(
    user_id: str,
    limit: int = 20,
):
    """
    Get all generated presentations.
    """

    db = get_database()

    cursor = db.presentations.find(
        {"user_id": user_id},
        sort=[("created_at", -1)],
        limit=limit,
    )

    presentations = []

    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        presentations.append(doc)

    return presentations


async def get_presentation_by_id(
    presentation_id: str,
    user_id: str,
):
    """
    Get one presentation.
    """

    db = get_database()

    doc = await db.presentations.find_one(
        {
            "_id": ObjectId(presentation_id),
            "user_id": user_id,
        }
    )

    if doc:
        doc["id"] = str(doc.pop("_id"))

    return doc