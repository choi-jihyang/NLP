from fastapi import APIRouter

from app.api.routes import (
    assignments,
    auth,
    chat,
    classes,
    enrollments,
    grading,
    health,
    me,
    payments,
    plans,
    solve,
    submissions,
)

api_router = APIRouter(prefix="/api")
for module in (health, auth, plans, payments, classes, enrollments, me, assignments, solve, submissions, chat, grading):
    api_router.include_router(module.router)
