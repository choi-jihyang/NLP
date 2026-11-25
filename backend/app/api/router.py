from fastapi import APIRouter

from app.api.routes import (
    assignments,
    auth,
    chat,
    classes,
    enrollments,
    health,
    me,
    payments,
    plans,
    solve,
    submissions,
)

api_router = APIRouter(prefix="/api")
for module in (health, auth, plans, payments, classes, enrollments, me, assignments, solve, submissions, chat):
    api_router.include_router(module.router)
# 기능별 라우터(chat, submissions, ...)는 구현하면서 여기에 추가
