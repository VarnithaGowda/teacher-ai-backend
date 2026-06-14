"""
ai_services/rubric_generator.py - AI Rubric Generation Service
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import logging

from database.connection import get_database
from prompts.rubric_prompt import rubric_prompt
from ai_services.gemini_client import get_llm

logger = logging.getLogger(__name__)


async def generate_rubric(
    user_id: str,
    assignment_title: str,
    assignment_type: str,
    subject: str,
    grade_level: str,
    total_marks: int,
    criteria: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> dict:
    """
    Generate a grading rubric using Gemini.
    """

    criteria_str = (
        ", ".join(criteria)
        if criteria
        else "Use standard criteria for this assignment type"
    )

    formatted_prompt = rubric_prompt.format(
        assignment_title=assignment_title,
        assignment_type=assignment_type,
        subject=subject,
        grade_level=grade_level,
        total_marks=total_marks,
        criteria=criteria_str,
        description=description or "Standard assignment",
        total_marks_90_100=f"{int(total_marks * 0.9)}-{total_marks}",
        total_marks_75_89=f"{int(total_marks * 0.75)}-{int(total_marks * 0.89)}",
        total_marks_60_74=f"{int(total_marks * 0.60)}-{int(total_marks * 0.74)}",
        total_marks_60=int(total_marks * 0.60),
    )

    llm = get_llm(temperature=0.5)
    logger.info(f"Generating rubric for: {assignment_title}")

    response = await llm.ainvoke(formatted_prompt)
    rubric_text = response.content

    # Remove unwanted sections if Gemini generates them
    sections_to_remove = [
        "## Grading Scale",
        "## Submission Requirements",
        "## Academic Integrity Note",
        "Grading Scale",
        "Submission Requirements",
        "Academic Integrity Note",
    ]

    for section in sections_to_remove:
        if section in rubric_text:
            rubric_text = rubric_text.split(section)[0].strip()

    # Remove excessive separator lines
    rubric_text = rubric_text.replace("---", "")
    rubric_text = rubric_text.replace("***", "")

    # Save to MongoDB
    db = get_database()

    doc = {
        "user_id": user_id,
        "assignment_title": assignment_title,
        "assignment_type": assignment_type,
        "subject": subject,
        "grade_level": grade_level,
        "total_marks": total_marks,
        "criteria": criteria or [],
        "description": description,
        "rubric": rubric_text,
        "created_at": datetime.utcnow(),
    }

    result = await db.rubrics.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "assignment_title": assignment_title,
        "assignment_type": assignment_type,
        "total_marks": total_marks,
        "rubric": rubric_text,
        "created_at": doc["created_at"],
    }


async def get_rubrics(user_id: str, limit: int = 20) -> list:
    """
    Retrieve all rubrics for a teacher.
    """
    db = get_database()

    cursor = db.rubrics.find(
        {"user_id": user_id},
        sort=[("created_at", -1)],
        limit=limit,
    )

    rubrics = []

    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        rubrics.append(doc)

    return rubrics


async def get_rubric_by_id(
    rubric_id: str,
    user_id: str,
) -> Optional[dict]:
    """
    Get a specific rubric by ID.
    """
    db = get_database()

    doc = await db.rubrics.find_one(
        {
            "_id": ObjectId(rubric_id),
            "user_id": user_id,
        }
    )

    if doc:
        doc["id"] = str(doc.pop("_id"))

    return doc