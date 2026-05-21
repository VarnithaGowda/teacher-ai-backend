"""
main.py - FastAPI application entry point
Teacher AI Platform - Backend Server
"""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from database.connection import connect_to_mongo, close_mongo_connection
from api import auth, lesson_plan, rubric, evaluation, chatbot, rag, analytics, workflow
from config import settings


# ─── Lifespan: startup / shutdown ─────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to MongoDB on startup, disconnect on shutdown."""
    await connect_to_mongo()
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    await close_mongo_connection()


# ─── App Instance ─────────────────────────────────────────────────
app = FastAPI(
    title="Teacher AI Platform API",
    description="AI-powered lesson planning, rubric generation, and student evaluation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS Middleware ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000", "https://teacher-ai-assist.netlify.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static Files (uploads) ───────────────────────────────────────
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ─── Register Routers ─────────────────────────────────────────────
app.include_router(auth.router,        prefix="/api/auth",       tags=["Authentication"])
app.include_router(lesson_plan.router, prefix="/api/lesson",     tags=["Lesson Plans"])
app.include_router(rubric.router,      prefix="/api/rubric",     tags=["Rubrics"])
app.include_router(evaluation.router,  prefix="/api/evaluation", tags=["Student Evaluation"])
app.include_router(chatbot.router,     prefix="/api/chat",       tags=["AI Chatbot"])
app.include_router(rag.router,         prefix="/api/rag",        tags=["RAG / Documents"])
app.include_router(analytics.router,   prefix="/api/analytics",  tags=["Analytics"])
app.include_router(workflow.router,    prefix="/api/workflow",   tags=["LangGraph Workflow"])


# ─── Health Check ─────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Teacher AI Platform API is running 🎓"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

