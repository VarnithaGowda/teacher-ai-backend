"""
api/evaluation.py - Student answer evaluation routes

Supports text input and file upload (PDF/DOCX) for student answers.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
import os

from auth.jwt_handler import get_current_user
from ai_services.evaluator import evaluate_student_answer, get_evaluations
from ai_services.rubric_generator import get_rubric_by_id
from utils.file_parser import parse_pdf, parse_docx, parse_text_file, get_file_type
from utils.helpers import save_upload_file

router = APIRouter()


@router.post("/evaluate", status_code=201)
async def evaluate_answer(
    student_name: str = Form(...),
    assignment_title: str = Form(...),
    total_marks: int = Form(50),
    rubric_text: Optional[str] = Form(None),
    rubric_id: Optional[str] = Form(None),
    model_answer: Optional[str] = Form(None),
    student_answer_text: Optional[str] = Form(None),
    student_answer_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Evaluate a student's answer using AI.
    
    Student answer can be provided as:
    - Text in `student_answer_text` field
    - File upload in `student_answer_file` (PDF, DOCX, TXT)
    
    Rubric can be provided as:
    - Text in `rubric_text` field
    - Reference to saved rubric via `rubric_id`
    """
    # ── Get student answer ──────────────────────────────────────
    student_answer = ""

    if student_answer_file:
        # Parse uploaded file
        file_path, filename = await save_upload_file(student_answer_file, current_user["id"])
        try:
            file_type = get_file_type(filename)
            if file_type == "pdf":
                student_answer = parse_pdf(file_path)
            elif file_type == "docx":
                student_answer = parse_docx(file_path)
            else:
                student_answer = parse_text_file(file_path)
        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)

    elif student_answer_text:
        student_answer = student_answer_text
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either student_answer_text or student_answer_file",
        )

    # ── Get rubric ──────────────────────────────────────────────
    rubric = ""

    if rubric_id:
        saved_rubric = await get_rubric_by_id(rubric_id, current_user["id"])
        if not saved_rubric:
            raise HTTPException(status_code=404, detail="Rubric not found")
        rubric = saved_rubric["rubric"]
        total_marks = saved_rubric.get("total_marks", total_marks)
    elif rubric_text:
        rubric = rubric_text
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either rubric_text or rubric_id",
        )

    # ── Run evaluation ──────────────────────────────────────────
    try:
        result = await evaluate_student_answer(
            user_id=current_user["id"],
            student_name=student_name,
            assignment_title=assignment_title,
            student_answer=student_answer,
            rubric_text=rubric,
            total_marks=total_marks,
            model_answer=model_answer,
            rubric_id=rubric_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/")
async def list_evaluations(current_user: dict = Depends(get_current_user)):
    """Get all student evaluations for the current teacher."""
    return await get_evaluations(current_user["id"])
