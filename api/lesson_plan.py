"""
api/lesson_plan.py - Lesson plan generation and retrieval routes
"""

from fastapi import APIRouter, Depends, HTTPException
from models.schemas import LessonPlanRequest, LessonPlanResponse
from auth.jwt_handler import get_current_user
from ai_services.lesson_planner import generate_lesson_plan, get_lesson_plans, get_lesson_plan_by_id

router = APIRouter()


@router.post("/generate", status_code=201)
async def create_lesson_plan(
    request: LessonPlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate an AI lesson plan.
    
    Provide subject, topic, grade level, duration, and difficulty.
    Returns a complete structured lesson plan in Markdown format.
    """
    try:
        result = await generate_lesson_plan(
            user_id=current_user["id"],
            subject=request.subject,
            topic=request.topic,
            grade_level=request.grade_level,
            duration_minutes=request.duration_minutes,
            difficulty=request.difficulty.value,
            learning_objectives=request.learning_objectives,
            additional_notes=request.additional_notes,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lesson plan generation failed: {str(e)}")


@router.get("/")
async def list_lesson_plans(current_user: dict = Depends(get_current_user)):
    """Get all lesson plans created by the current teacher."""
    return await get_lesson_plans(current_user["id"])


@router.get("/{plan_id}")
async def get_lesson_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific lesson plan by ID."""
    plan = await get_lesson_plan_by_id(plan_id, current_user["id"])
    if not plan:
        raise HTTPException(status_code=404, detail="Lesson plan not found")
    return plan
