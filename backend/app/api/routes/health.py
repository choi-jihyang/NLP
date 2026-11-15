from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """서버 상태와 현재 쓰는 LLM·분류기 종류."""
    s = get_settings()
    return {"status": "ok", "llm_provider": s.llm_provider, "classifier": s.classifier}
