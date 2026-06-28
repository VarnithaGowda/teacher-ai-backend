"""
ai_services/question_paper_generator.py
AI Question Paper Generation Service
"""

from typing import List
from datetime import datetime
from bson import ObjectId
import logging

from database.connection import get_database
from prompts.question_paper_prompt import question_paper_prompt
from ai_services.gemini_client import get_llm

logger = logging.getLogger(__name__)


async def generate_question_paper(
    user_id: str,
    subject: str,
    grade_level: str,
    exam_type: str,
    difficulty: str,
    total_marks: int,
    duration: int,
    topics: List[str],
) -> dict:
    """
    Generate an AI Question Paper using Gemini.
    """

    topics_text = "\n".join(f"- {topic}" for topic in topics)

    formatted_prompt = question_paper_prompt.format(
        subject=subject,
        grade_level=grade_level,
        exam_type=exam_type,
        difficulty=difficulty,
        total_marks=total_marks,
        duration=duration,
        topics=topics_text,
    )

    llm = get_llm(temperature=0.6)

    logger.info(
        f"Generating Question Paper for {subject} ({grade_level})"
    )

    response = await llm.ainvoke(formatted_prompt)

    question_paper = response.content

    db = get_database()

    doc = {
        "user_id": user_id,
        "subject": subject,
        "grade_level": grade_level,
        "exam_type": exam_type,
        "difficulty": difficulty,
        "total_marks": total_marks,
        "duration": duration,
        "topics": topics,
        "question_paper": question_paper,
        "created_at": datetime.utcnow(),
    }

    result = await db.question_papers.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "subject": subject,
        "grade_level": grade_level,
        "exam_type": exam_type,
        "difficulty": difficulty,
        "total_marks": total_marks,
        "duration": duration,
        "question_paper": question_paper,
        "created_at": doc["created_at"],
    }


async def get_question_papers(
    user_id: str,
    limit: int = 20,
) -> list:
    """
    Get all generated question papers.
    """

    db = get_database()

    cursor = db.question_papers.find(
        {"user_id": user_id},
        sort=[("created_at", -1)],
        limit=limit,
    )

    papers = []

    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        papers.append(doc)

    return papers


async def get_question_paper_by_id(
    paper_id: str,
    user_id: str,
):
    """
    Retrieve one question paper.
    """

    db = get_database()

    doc = await db.question_papers.find_one(
        {
            "_id": ObjectId(paper_id),
            "user_id": user_id,
        }
    )

    if doc:
        doc["id"] = str(doc.pop("_id"))

    return doc