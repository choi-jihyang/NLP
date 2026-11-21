from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import install_error_handling
from app.api.router import api_router
from app.core.config import get_settings
from app.db.init_db import init_db
from app.db.session import engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db(engine)
    yield


def build_app() -> FastAPI:
    app = FastAPI(title="ThinkGuard API", version="0.1.0", lifespan=lifespan)
    # 에러 처리를 먼저 등록해 CORS가 그 바깥에 오게 한다 → 401·500 등 에러 응답에도 CORS 헤더가 붙는다
    install_error_handling(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = build_app()
