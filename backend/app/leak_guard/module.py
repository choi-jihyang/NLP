"""NLP 팀의 Python 모듈을 직접 불러와 쓰는 누출 검사기 (LEAK_GUARD_MODULE)."""

import anyio

from app.classifier.module import load_function
from app.leak_guard.base import LeakCheckResult, LeakGuard
from app.schemas.chat import ChatTurn


class ModuleLeakGuard(LeakGuard):
    def __init__(self, path: str):
        self._fn = load_function(path)

    async def check(self, reply: str, history: list[ChatTurn]) -> LeakCheckResult:
        history_dicts = [t.model_dump() for t in history]
        raw = await anyio.to_thread.run_sync(self._fn, reply, history_dicts)
        return LeakCheckResult.model_validate(raw)
