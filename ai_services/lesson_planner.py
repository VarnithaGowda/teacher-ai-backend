"""
ai_services/lesson_planner.py - AI Lesson Plan Generation Service

Uses LangChain + Gemini to generate structured lesson plans.
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import logging

from database.connection import get_database
from prompts.lesson_plan_prompt import lesson_plan_prompt
from ai_services.gemini_client import get_llm

logger = logging.getLogger(__name__)


async def generate_lesson_plan(
    user_id: str,
    subject: str,
    topic: str,
    grade_level: str,
    duration_minutes: int,
    difficulty: str = "intermediate",
    learning_objectives: Optional[List[str]] = None,
    additional_notes: Optional[str] = None,
) -> dict:
    """
    Generate a complete lesson plan using Gemini via LangChain.
    
    Args:
        user_id: Teacher's user ID (for saving to DB)
        subject: e.g., "Mathematics"
        topic: e.g., "Quadratic Equations"
        grade_level: e.g., "Grade 10"
        duration_minutes: Lesson duration (15-180)
        difficulty: beginner/intermediate/advanced
        learning_objectives: Optional list of custom objectives
        additional_notes: Any extra context for the AI
    
    Returns:
        Dict with lesson plan data including the generated markdown
    """
    # Format learning objectives for the prompt
    objectives_str = (
        "\n".join(f"- {obj}" for obj in learning_objectives)
        if learning_objectives
        else "Generate appropriate objectives based on the topic"
    )

    # Build the prompt using LangChain PromptTemplate
    formatted_prompt = lesson_plan_prompt.format(
        subject=subject,
        topic=topic,
        grade_level=grade_level,
        duration_minutes=duration_minutes,
        difficulty=difficulty,
        learning_objectives=objectives_str,
        additional_notes=additional_notes or "None",
    )

    # Call Gemini via LangChain
    llm = get_llm(temperature=0.7)
    logger.info(f"Generating lesson plan for: {subject} - {topic}")
    response = await llm.ainvoke(formatted_prompt)
    lesson_plan_text = response.content

    # Save to MongoDB
    db = get_database()
    doc = {
        "user_id": user_id,
        "subject": subject,
        "topic": topic,
        "grade_level": grade_level,
        "duration_minutes": duration_minutes,
        "difficulty": difficulty,
        "learning_objectives": learning_objectives or [],
        "additional_notes": additional_notes,
        "lesson_plan": lesson_plan_text,
        "created_at": datetime.utcnow(),
    }
    result = await db.lesson_plans.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "subject": subject,
        "topic": topic,
        "grade_level": grade_level,
        "duration_minutes": duration_minutes,
        "difficulty": difficulty,
        "lesson_plan": lesson_plan_text,
        "created_at": doc["created_at"],
    }


async def get_lesson_plans(user_id: str, limit: int = 20) -> list:
    """Retrieve all lesson plans for a teacher."""
    db = get_database()
    cursor = db.lesson_plans.find(
        {"user_id": user_id},
        sort=[("created_at", -1)],
        limit=limit,
    )
    plans = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        plans.append(doc)
    return plans


async def get_lesson_plan_by_id(plan_id: str, user_id: str) -> Optional[dict]:
    """Get a specific lesson plan by ID."""
    db = get_database()
    doc = await db.lesson_plans.find_one({
        "_id": ObjectId(plan_id),
        "user_id": user_id,
    })
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc
