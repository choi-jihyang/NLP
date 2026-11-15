from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
# 기능별 라우터(auth, classes, assignments, chat, ...)는 구현하면서 여기에 추가
