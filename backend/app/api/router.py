from fastapi import APIRouter

from app.api.routes import auth, classes, enrollments, health, me, payments, plans

api_router = APIRouter(prefix="/api")
for module in (health, auth, plans, payments, classes, enrollments, me):
    api_router.include_router(module.router)
# 기능별 라우터(assignments, chat, ...)는 구현하면서 여기에 추가
