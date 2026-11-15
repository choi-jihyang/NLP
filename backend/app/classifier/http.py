"""NLP 팀의 FastAPI 엔드포인트를 호출하는 분류기 (CLASSIFIER=http)."""

import httpx

from app.classifier.base import ClassificationResult, Classifier
from app.schemas.chat import ChatTurn


class HttpClassifier(Classifier):
    def __init__(self, url: str, timeout: float = 10.0):
        self._url = url
        self._timeout = timeout

    async def classify(self, message: str, history: list[ChatTurn]) -> ClassificationResult:
        payload = {"message": message, "history": [t.model_dump() for t in history]}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            res = await client.post(self._url, json=payload)
            res.raise_for_status()
        return ClassificationResult.model_validate(res.json())
