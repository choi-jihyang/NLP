from fastapi import APIRouter

from app.api.routes import auth, health

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
# 기능별 라우터(classes, assignments, chat, ...)는 구현하면서 여기에 추가
