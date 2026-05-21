"""
api/workflow.py - LangGraph workflow routes

Exposes the multi-step teacher workflow:
Upload Syllabus → Extract Topics → Generate Lesson Plan → Generate Rubric → Generate Assignment
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
import os

from auth.jwt_handler import get_current_user
from workflows.teacher_workflow import run_teacher_workflow
from utils.file_parser import parse_pdf, parse_docx, parse_text_file, get_file_type
from utils.helpers import save_upload_file
from database.connection import get_database

router = APIRouter()


@router.post("/run", status_code=201)
async def run_workflow(
    subject: str = Form(...),
    grade_level: str = Form(...),
    syllabus_text: Optional[str] = Form(None),
    syllabus_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Run the complete LangGraph teacher workflow.
    
    Steps:
    1. Extract topics from syllabus
    2. Generate lesson plan for primary topic
    3. Generate grading rubric
    4. Generate student assignment
    
    Provide syllabus as either text or file upload (PDF/DOCX/TXT).
    """
    # Get syllabus content
    syllabus = ""

    if syllabus_file:
        file_path, filename = await save_upload_file(syllabus_file, current_user["id"])
        try:
            file_type = get_file_type(filename)
            if file_type == "pdf":
                syllabus = parse_pdf(file_path)
            elif file_type == "docx":
                syllabus = parse_docx(file_path)
            else:
                syllabus = parse_text_file(file_path)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    elif syllabus_text:
        syllabus = syllabus_text
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either syllabus_text or syllabus_file",
        )

    if len(syllabus.strip()) < 50:
        raise HTTPException(
            status_code=422,
            detail="Syllabus content is too short. Please provide more content.",
        )

    # Run the LangGraph workflow
    try:
        result = await run_teacher_workflow(
            user_id=current_user["id"],
            subject=subject,
            grade_level=grade_level,
            syllabus_text=syllabus,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")


@router.get("/history")
async def get_workflow_history(current_user: dict = Depends(get_current_user)):
    """Get all workflow runs for the current teacher."""
    db = get_database()
    cursor = db.workflows.find(
        {"user_id": current_user["id"]},
        sort=[("created_at", -1)],
        limit=20,
    )
    workflows = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        workflows.append(doc)
    return workflows


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific workflow result by ID."""
    db = get_database()
    doc = await db.workflows.find_one({
        "workflow_id": workflow_id,
        "user_id": current_user["id"],
    })
    if not doc:
        raise HTTPException(status_code=404, detail="Workflow not found")
    doc["id"] = str(doc.pop("_id"))
    return doc
