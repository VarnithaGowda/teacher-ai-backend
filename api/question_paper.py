"""
api/question_paper.py
Question Paper API Routes
"""

from fastapi import APIRouter, Depends, HTTPException

from auth.jwt_handler import get_current_user
from models.schemas import (
    QuestionPaperRequest,
    QuestionPaperResponse,
)
from ai_services.question_paper_generator import (
    generate_question_paper,
    get_question_papers,
    get_question_paper_by_id,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=QuestionPaperResponse,
    status_code=201,
)
async def create_question_paper(
    request: QuestionPaperRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate an AI Question Paper.
    """
    try:
        result = await generate_question_paper(
            user_id=current_user["id"],
            subject=request.subject,
            grade_level=request.grade_level,
            exam_type=request.exam_type,
            difficulty=request.difficulty.value,
            total_marks=request.total_marks,
            duration=request.duration,
            topics=request.topics,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Question paper generation failed: {str(e)}",
        )


@router.get("/")
async def list_question_papers(
    current_user: dict = Depends(get_current_user),
):
    """
    Get all generated question papers.
    """
    return await get_question_papers(current_user["id"])


@router.get("/{paper_id}")
async def get_question_paper(
    paper_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get one question paper.
    """

    paper = await get_question_paper_by_id(
        paper_id,
        current_user["id"],
    )

    if not paper:
        raise HTTPException(
            status_code=404,
            detail="Question paper not found",
        )

    return paper