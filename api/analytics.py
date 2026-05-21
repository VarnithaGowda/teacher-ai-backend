"""
api/analytics.py - Analytics and dashboard data routes
"""

from fastapi import APIRouter, Depends
from auth.jwt_handler import get_current_user
from database.connection import get_database
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(current_user: dict = Depends(get_current_user)):
    """
    Get dashboard analytics summary for the current teacher.
    
    Returns counts of lesson plans, rubrics, evaluations, documents,
    average student scores, and recent activity.
    """
    db = get_database()
    user_id = current_user["id"]

    # Run all counts in parallel using asyncio.gather
    import asyncio
    (
        lesson_count,
        rubric_count,
        eval_count,
        doc_count,
    ) = await asyncio.gather(
        db.lesson_plans.count_documents({"user_id": user_id}),
        db.rubrics.count_documents({"user_id": user_id}),
        db.evaluations.count_documents({"user_id": user_id}),
        db.documents.count_documents({"user_id": user_id}),
    )

    # Calculate average score from evaluations
    avg_score = None
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$percentage"}}},
    ]
    async for doc in db.evaluations.aggregate(pipeline):
        avg_score = round(doc["avg"], 1)

    # Get recent activity (last 10 items across all collections)
    recent_activity = []

    # Recent lesson plans
    async for doc in db.lesson_plans.find(
        {"user_id": user_id},
        {"topic": 1, "subject": 1, "created_at": 1},
        sort=[("created_at", -1)],
        limit=3,
    ):
        recent_activity.append({
            "type": "lesson_plan",
            "title": f"Lesson Plan: {doc.get('topic', 'Unknown')}",
            "subject": doc.get("subject"),
            "created_at": doc.get("created_at"),
        })

    # Recent evaluations
    async for doc in db.evaluations.find(
        {"user_id": user_id},
        {"student_name": 1, "assignment_title": 1, "grade": 1, "created_at": 1},
        sort=[("created_at", -1)],
        limit=3,
    ):
        recent_activity.append({
            "type": "evaluation",
            "title": f"Evaluated: {doc.get('student_name', 'Student')}",
            "grade": doc.get("grade"),
            "created_at": doc.get("created_at"),
        })

    # Recent rubrics
    async for doc in db.rubrics.find(
        {"user_id": user_id},
        {"assignment_title": 1, "created_at": 1},
        sort=[("created_at", -1)],
        limit=2,
    ):
        recent_activity.append({
            "type": "rubric",
            "title": f"Rubric: {doc.get('assignment_title', 'Unknown')}",
            "created_at": doc.get("created_at"),
        })

    # Sort by date
    recent_activity.sort(
        key=lambda x: x.get("created_at") or datetime.min,
        reverse=True,
    )

    return {
        "total_lesson_plans": lesson_count,
        "total_rubrics": rubric_count,
        "total_evaluations": eval_count,
        "total_documents": doc_count,
        "average_score": avg_score,
        "recent_activity": recent_activity[:8],
    }


@router.get("/evaluations/chart")
async def get_evaluation_chart_data(current_user: dict = Depends(get_current_user)):
    """
    Get evaluation data formatted for charts.
    Returns grade distribution and score trends.
    """
    db = get_database()
    user_id = current_user["id"]

    # Grade distribution
    grade_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$grade", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    grade_dist = {}
    async for doc in db.evaluations.aggregate(grade_pipeline):
        grade_dist[doc["_id"]] = doc["count"]

    # Score trend (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    trend_pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": thirty_days_ago}}},
        {"$sort": {"created_at": 1}},
        {"$project": {
            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "percentage": 1,
            "student_name": 1,
            "grade": 1,
        }},
    ]
    score_trend = []
    async for doc in db.evaluations.aggregate(trend_pipeline):
        doc.pop("_id", None)
        score_trend.append(doc)

    return {
        "grade_distribution": grade_dist,
        "score_trend": score_trend,
    }
