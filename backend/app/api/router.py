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
    reports,
    solve,
    submissions,
)

api_router = APIRouter(prefix="/api")
MODULES = (health, auth, plans, payments, classes, enrollments, me, assignments, solve, submissions, chat, grading,
           reports)
for module in MODULES:
    api_router.include_router(module.router)
