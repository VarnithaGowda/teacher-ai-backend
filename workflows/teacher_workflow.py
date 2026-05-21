"""
workflows/teacher_workflow.py - LangGraph Multi-Step Teacher Workflow

Implements the pipeline:
  Upload Syllabus → Extract Topics → Generate Lesson Plan → Generate Rubric → Generate Assignment

LangGraph uses a state machine where each node processes and updates shared state.
"""

import json
import re
from typing import TypedDict, List, Optional, Annotated
from datetime import datetime
import logging

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from ai_services.gemini_client import get_llm
from prompts.workflow_prompt import (
    topic_extraction_prompt,
    workflow_lesson_plan_prompt,
    workflow_rubric_prompt,
    workflow_assignment_prompt,
)
from database.connection import get_database

logger = logging.getLogger(__name__)


# ─── Workflow State ───────────────────────────────────────────────
class WorkflowState(TypedDict):
    """
    Shared state passed between all workflow nodes.
    Each node reads from and writes to this state.
    """
    # Input
    user_id: str
    subject: str
    grade_level: str
    syllabus_text: str
    workflow_id: str

    # Intermediate outputs
    topics_extracted: List[str]
    primary_topic: str
    subtopics: List[str]

    # Final outputs
    lesson_plan: str
    rubric: str
    assignment: str

    # Status tracking
    status: str
    error: Optional[str]


# ─── Node 1: Extract Topics ───────────────────────────────────────
async def extract_topics_node(state: WorkflowState) -> WorkflowState:
    """
    Node 1: Parse the syllabus and extract all topics.
    Uses Gemini to intelligently identify topics from unstructured text.
    """
    logger.info(f"[Workflow {state['workflow_id']}] Step 1: Extracting topics")

    try:
        formatted_prompt = topic_extraction_prompt.format(
            subject=state["subject"],
            grade_level=state["grade_level"],
            syllabus_text=state["syllabus_text"][:3000],  # Limit to avoid token overflow
        )

        llm = get_llm(temperature=0.3)
        response = await llm.ainvoke(formatted_prompt)
        response_text = response.content

        # Try to parse JSON from response
        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        topics_data = {}
        if json_match:
            try:
                topics_data = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Extract topic list
        main_topics = topics_data.get("main_topics", [])
        if main_topics:
            topics_list = [t["topic"] for t in main_topics]
            primary_topic = topics_list[0] if topics_list else state["subject"]
            subtopics = main_topics[0].get("subtopics", []) if main_topics else []
        else:
            # Fallback: extract topics from plain text
            lines = [l.strip() for l in response_text.split("\n") if l.strip() and len(l.strip()) > 3]
            topics_list = lines[:10]
            primary_topic = topics_list[0] if topics_list else state["subject"]
            subtopics = topics_list[1:4]

        return {
            **state,
            "topics_extracted": topics_list,
            "primary_topic": primary_topic,
            "subtopics": subtopics,
            "status": "topics_extracted",
        }

    except Exception as e:
        logger.error(f"Topic extraction failed: {e}")
        return {**state, "error": str(e), "status": "failed"}


# ─── Node 2: Generate Lesson Plan ────────────────────────────────
async def generate_lesson_plan_node(state: WorkflowState) -> WorkflowState:
    """
    Node 2: Generate a lesson plan for the primary topic.
    """
    if state.get("status") == "failed":
        return state

    logger.info(f"[Workflow {state['workflow_id']}] Step 2: Generating lesson plan")

    try:
        subtopics_str = ", ".join(state.get("subtopics", [])[:5]) or "Core concepts"

        formatted_prompt = workflow_lesson_plan_prompt.format(
            subject=state["subject"],
            grade_level=state["grade_level"],
            primary_topic=state["primary_topic"],
            subtopics=subtopics_str,
        )

        llm = get_llm(temperature=0.7)
        response = await llm.ainvoke(formatted_prompt)

        return {
            **state,
            "lesson_plan": response.content,
            "status": "lesson_plan_generated",
        }

    except Exception as e:
        logger.error(f"Lesson plan generation failed: {e}")
        return {**state, "error": str(e), "status": "failed"}


# ─── Node 3: Generate Rubric ──────────────────────────────────────
async def generate_rubric_node(state: WorkflowState) -> WorkflowState:
    """
    Node 3: Generate a rubric based on the lesson plan.
    """
    if state.get("status") == "failed":
        return state

    logger.info(f"[Workflow {state['workflow_id']}] Step 3: Generating rubric")

    try:
        # Summarize lesson plan for the rubric prompt (first 500 chars)
        lesson_summary = state["lesson_plan"][:500] + "..."

        formatted_prompt = workflow_rubric_prompt.format(
            lesson_plan_summary=lesson_summary,
            subject=state["subject"],
            grade_level=state["grade_level"],
        )

        llm = get_llm(temperature=0.5)
        response = await llm.ainvoke(formatted_prompt)

        return {
            **state,
            "rubric": response.content,
            "status": "rubric_generated",
        }

    except Exception as e:
        logger.error(f"Rubric generation failed: {e}")
        return {**state, "error": str(e), "status": "failed"}


# ─── Node 4: Generate Assignment ─────────────────────────────────
async def generate_assignment_node(state: WorkflowState) -> WorkflowState:
    """
    Node 4: Generate a student assignment based on the rubric.
    """
    if state.get("status") == "failed":
        return state

    logger.info(f"[Workflow {state['workflow_id']}] Step 4: Generating assignment")

    try:
        rubric_summary = state["rubric"][:400] + "..."

        formatted_prompt = workflow_assignment_prompt.format(
            topic=state["primary_topic"],
            subject=state["subject"],
            grade_level=state["grade_level"],
            rubric_summary=rubric_summary,
        )

        llm = get_llm(temperature=0.7)
        response = await llm.ainvoke(formatted_prompt)

        return {
            **state,
            "assignment": response.content,
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Assignment generation failed: {e}")
        return {**state, "error": str(e), "status": "failed"}


# ─── Node 5: Save Results ─────────────────────────────────────────
async def save_results_node(state: WorkflowState) -> WorkflowState:
    """
    Node 5: Save the complete workflow results to MongoDB.
    """
    logger.info(f"[Workflow {state['workflow_id']}] Step 5: Saving results")

    try:
        db = get_database()
        await db.workflows.update_one(
            {"workflow_id": state["workflow_id"]},
            {"$set": {
                "topics_extracted": state.get("topics_extracted", []),
                "lesson_plan": state.get("lesson_plan", ""),
                "rubric": state.get("rubric", ""),
                "assignment": state.get("assignment", ""),
                "status": state.get("status", "completed"),
                "completed_at": datetime.utcnow(),
            }},
        )
    except Exception as e:
        logger.error(f"Failed to save workflow results: {e}")

    return state


# ─── Conditional Edge: Check for Errors ──────────────────────────
def should_continue(state: WorkflowState) -> str:
    """Route to END if there's an error, otherwise continue."""
    if state.get("status") == "failed":
        return "save_and_end"
    return "continue"


# ─── Build the LangGraph ──────────────────────────────────────────
def build_teacher_workflow() -> StateGraph:
    """
    Construct the LangGraph workflow graph.
    
    Graph structure:
    extract_topics → generate_lesson_plan → generate_rubric → generate_assignment → save_results → END
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("extract_topics", extract_topics_node)
    workflow.add_node("generate_lesson_plan", generate_lesson_plan_node)
    workflow.add_node("generate_rubric", generate_rubric_node)
    workflow.add_node("generate_assignment", generate_assignment_node)
    workflow.add_node("save_results", save_results_node)

    # Set entry point
    workflow.set_entry_point("extract_topics")

    # Add edges (sequential flow)
    workflow.add_edge("extract_topics", "generate_lesson_plan")
    workflow.add_edge("generate_lesson_plan", "generate_rubric")
    workflow.add_edge("generate_rubric", "generate_assignment")
    workflow.add_edge("generate_assignment", "save_results")
    workflow.add_edge("save_results", END)

    return workflow.compile()


# ─── Run Workflow ─────────────────────────────────────────────────
async def run_teacher_workflow(
    user_id: str,
    subject: str,
    grade_level: str,
    syllabus_text: str,
) -> dict:
    """
    Execute the full teacher workflow.
    
    Args:
        user_id: Teacher's user ID
        subject: Subject name
        grade_level: Grade level
        syllabus_text: Full syllabus content
    
    Returns:
        Complete workflow results
    """
    import uuid
    workflow_id = str(uuid.uuid4())

    # Save initial workflow record
    db = get_database()
    await db.workflows.insert_one({
        "workflow_id": workflow_id,
        "user_id": user_id,
        "subject": subject,
        "grade_level": grade_level,
        "status": "running",
        "created_at": datetime.utcnow(),
    })

    # Build and run the graph
    graph = build_teacher_workflow()

    initial_state: WorkflowState = {
        "user_id": user_id,
        "subject": subject,
        "grade_level": grade_level,
        "syllabus_text": syllabus_text,
        "workflow_id": workflow_id,
        "topics_extracted": [],
        "primary_topic": "",
        "subtopics": [],
        "lesson_plan": "",
        "rubric": "",
        "assignment": "",
        "status": "running",
        "error": None,
    }

    # Execute the workflow
    final_state = await graph.ainvoke(initial_state)

    return {
        "workflow_id": workflow_id,
        "subject": subject,
        "topics_extracted": final_state.get("topics_extracted", []),
        "lesson_plan": final_state.get("lesson_plan", ""),
        "rubric": final_state.get("rubric", ""),
        "assignment": final_state.get("assignment", ""),
        "status": final_state.get("status", "completed"),
        "created_at": datetime.utcnow(),
    }
