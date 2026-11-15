"""NLP 팀의 Python 모듈을 직접 불러와 쓰는 분류기 (CLASSIFIER=module)."""

import importlib
from collections.abc import Callable
from typing import Any

import anyio

from app.classifier.base import ClassificationResult, Classifier
from app.schemas.chat import ChatTurn


def _load(path: str) -> Callable[..., Any]:
    """'패키지.모듈:함수' 문자열로 함수를 불러온다."""
    module_name, _, func_name = path.partition(":")
    if not func_name:
        raise ValueError(f"CLASSIFIER_MODULE 형식은 '모듈:함수' 입니다: {path!r}")
    return getattr(importlib.import_module(module_name), func_name)


class ModuleClassifier(Classifier):
    def __init__(self, path: str):
        self._fn = _load(path)

    async def classify(self, message: str, history: list[ChatTurn]) -> ClassificationResult:
        history_dicts = [t.model_dump() for t in history]
        # NLP 모듈은 동기 함수로 가정 → 이벤트 루프를 막지 않게 스레드에서 실행
        raw = await anyio.to_thread.run_sync(self._fn, message, history_dicts)
        return ClassificationResult.model_validate(raw)
