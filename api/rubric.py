"""
api/rubric.py - Rubric generation and retrieval routes
"""

from fastapi import APIRouter, Depends, HTTPException
from models.schemas import RubricRequest
from auth.jwt_handler import get_current_user
from ai_services.rubric_generator import generate_rubric, get_rubrics, get_rubric_by_id

router = APIRouter()


@router.post("/generate", status_code=201)
async def create_rubric(
    request: RubricRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate an AI grading rubric.
    
    Supports essay, coding, presentation, quiz, and project types.
    Returns a detailed rubric with criteria and performance descriptors.
    """
    try:
        result = await generate_rubric(
            user_id=current_user["id"],
            assignment_title=request.assignment_title,
            assignment_type=request.assignment_type.value,
            subject=request.subject,
            grade_level=request.grade_level,
            total_marks=request.total_marks,
            criteria=request.criteria,
            description=request.description,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rubric generation failed: {str(e)}")


@router.get("/")
async def list_rubrics(current_user: dict = Depends(get_current_user)):
    """Get all rubrics created by the current teacher."""
    return await get_rubrics(current_user["id"])


@router.get("/{rubric_id}")
async def get_rubric(
    rubric_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific rubric by ID."""
    rubric = await get_rubric_by_id(rubric_id, current_user["id"])
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return rubric
