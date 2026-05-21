"""
ai_services/evaluator.py - AI Student Answer Evaluation Service
"""

import json
import re
import asyncio
from typing import Optional
from datetime import datetime
from bson import ObjectId
import logging

from database.connection import get_database
from prompts.evaluation_prompt import evaluation_prompt
from ai_services.gemini_client import get_llm

logger = logging.getLogger(__name__)


def _extract_json_from_response(text: str) -> dict:
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    json_match = re.search(r"\{[^{}]*\"marks_obtained\"[^{}]*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    return {"marks_obtained": 0, "total_marks": 50, "percentage": 0,
            "grade": "N/A", "strengths": [], "improvements": []}


def _calculate_grade(percentage: float) -> str:
    if percentage >= 90: return "A+"
    elif percentage >= 80: return "A"
    elif percentage >= 75: return "B+"
    elif percentage >= 65: return "B"
    elif percentage >= 60: return "C"
    elif percentage >= 50: return "D"
    else: return "F"


async def evaluate_student_answer(
    user_id: str,
    student_name: str,
    assignment_title: str,
    student_answer: str,
    rubric_text: str,
    total_marks: int = 50,
    model_answer: Optional[str] = None,
    rubric_id: Optional[str] = None,
) -> dict:
    formatted_prompt = evaluation_prompt.format(
        assignment_title=assignment_title,
        student_name=student_name,
        rubric=rubric_text,
        model_answer=model_answer or "Not provided",
        student_answer=student_answer,
        total_marks=total_marks,
    )

    llm = get_llm(temperature=0.3)
    logger.info(f"Evaluating answer for student: {student_name}")

    full_feedback = ""
    for attempt in range(3):
        try:
            response = await llm.ainvoke(formatted_prompt)
            full_feedback = response.content
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                wait = 35 * (attempt + 1)
                logger.warning(f"Rate limit hit, retrying in {wait}s...")
                await asyncio.sleep(wait)
            else:
                raise

    if not full_feedback:
        raise ValueError("No response received from AI model")

    eval_data = _extract_json_from_response(full_feedback)
    marks_obtained = float(eval_data.get("marks_obtained", 0))
    percentage = (marks_obtained / total_marks * 100) if total_marks > 0 else 0
    grade = _calculate_grade(percentage)

    db = get_database()
    doc = {
        "user_id": user_id,
        "student_name": student_name,
        "assignment_title": assignment_title,
        "rubric_id": rubric_id,
        "marks_obtained": marks_obtained,
        "total_marks": total_marks,
        "percentage": round(percentage, 2),
        "grade": grade,
        "feedback": full_feedback,
        "strengths": eval_data.get("strengths", []),
        "improvements": eval_data.get("improvements", []),
        "created_at": datetime.utcnow(),
    }
    result = await db.evaluations.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "student_name": student_name,
        "assignment_title": assignment_title,
        "marks_obtained": marks_obtained,
        "total_marks": total_marks,
        "percentage": round(percentage, 2),
        "grade": grade,
        "feedback": full_feedback,
        "strengths": eval_data.get("strengths", []),
        "improvements": eval_data.get("improvements", []),
        "created_at": doc["created_at"],
    }


async def get_evaluations(user_id: str, limit: int = 50) -> list:
    db = get_database()
    cursor = db.evaluations.find({"user_id": user_id}, sort=[("created_at", -1)], limit=limit)
    evals = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        evals.append(doc)
    return evals