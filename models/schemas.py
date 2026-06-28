"""
models/schemas.py - Pydantic request/response schemas
All API input validation and output serialization happens here.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────

class DifficultyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class AssignmentType(str, Enum):
    essay = "essay"
    coding = "coding"
    presentation = "presentation"
    quiz = "quiz"
    project = "project"


# ─── Auth Schemas ─────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    school: Optional[str] = None
    subject: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    school: Optional[str] = None
    subject: Optional[str] = None
    created_at: datetime


# ─── Lesson Plan Schemas ──────────────────────────────────────────

class LessonPlanRequest(BaseModel):
    subject: str = Field(..., example="Mathematics")
    topic: str = Field(..., example="Quadratic Equations")
    grade_level: str = Field(..., example="Grade 10")
    duration_minutes: int = Field(..., ge=15, le=180, example=60)
    difficulty: DifficultyLevel = DifficultyLevel.intermediate
    learning_objectives: Optional[List[str]] = None
    additional_notes: Optional[str] = None

class LessonPlanResponse(BaseModel):
    id: str
    subject: str
    topic: str
    grade_level: str
    duration_minutes: int
    difficulty: str
    lesson_plan: str          # Full markdown lesson plan from AI
    created_at: datetime


# ─── Rubric Schemas ───────────────────────────────────────────────

class RubricRequest(BaseModel):
    assignment_title: str = Field(..., example="Python OOP Project")
    assignment_type: AssignmentType = AssignmentType.coding
    subject: str = Field(..., example="Computer Science")
    grade_level: str = Field(..., example="Grade 11")
    total_marks: int = Field(..., ge=10, le=100, example=50)
    criteria: Optional[List[str]] = None   # Custom criteria (optional)
    description: Optional[str] = None

class RubricResponse(BaseModel):
    id: str
    assignment_title: str
    assignment_type: str
    total_marks: int
    rubric: str               # Full markdown rubric from AI
    created_at: datetime


# ─── Evaluation Schemas ───────────────────────────────────────────

class EvaluationRequest(BaseModel):
    student_name: str
    assignment_title: str
    rubric_id: Optional[str] = None       # Reference existing rubric
    rubric_text: Optional[str] = None     # Or provide rubric inline
    model_answer: Optional[str] = None    # Optional model answer
    # student_answer comes via file upload or text field

class EvaluationResponse(BaseModel):
    id: str
    student_name: str
    assignment_title: str
    marks_obtained: float
    total_marks: float
    percentage: float
    grade: str
    feedback: str             # Detailed AI feedback
    strengths: List[str]
    improvements: List[str]
    created_at: datetime


# ─── Chat Schemas ─────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str                 # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None     # For conversation continuity
    use_rag: bool = True                 # Whether to use uploaded docs

class ChatResponse(BaseModel):
    session_id: str
    message: str              # AI response
    sources: Optional[List[str]] = None  # RAG source documents


# ─── RAG / Document Schemas ───────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    message: str

class DocumentListResponse(BaseModel):
    documents: List[Dict[str, Any]]


# ─── Workflow Schemas ─────────────────────────────────────────────

class WorkflowRequest(BaseModel):
    subject: str
    grade_level: str
    syllabus_text: Optional[str] = None  # Inline syllabus text
    # OR upload a PDF via separate endpoint

class WorkflowResponse(BaseModel):
    workflow_id: str
    subject: str
    topics_extracted: List[str]
    lesson_plan: str
    rubric: str
    assignment: str
    status: str
    created_at: datetime


# ─── Analytics Schemas ────────────────────────────────────────────

class AnalyticsSummary(BaseModel):
    total_lesson_plans: int
    total_rubrics: int
    total_evaluations: int
    total_documents: int
    average_score: Optional[float] = None
    recent_activity: List[Dict[str, Any]]

# ─── Question Paper Schemas ───────────────────────────────────────

class QuestionPaperRequest(BaseModel):
    subject: str = Field(..., example="Computer Science")
    grade_level: str = Field(..., example="Grade 10")
    exam_type: str = Field(..., example="Mid Semester")
    difficulty: DifficultyLevel = DifficultyLevel.intermediate
    total_marks: int = Field(..., ge=20, le=100, example=50)
    duration: int = Field(..., ge=30, le=180, example=90)
    topics: List[str] = Field(
        ...,
        example=[
            "Arrays",
            "Linked Lists",
            "Stacks",
            "Queues"
        ]
    )


class QuestionPaperResponse(BaseModel):
    id: str
    subject: str
    grade_level: str
    exam_type: str
    difficulty: str
    total_marks: int
    duration: int
    question_paper: str
    created_at: datetime