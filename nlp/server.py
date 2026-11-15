"""분류기를 HTTP로 노출하는 서버 (백엔드 CLASSIFIER=http 용).

실행: uvicorn server:app --port 8001   (nlp/ 디렉터리에서)
"""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from thinkguard_nlp.classifier import classify

app = FastAPI(title="ThinkGuard NLP Classifier")


class Turn(BaseModel):
    role: Literal["student", "assistant"]
    content: str


class ClassifyRequest(BaseModel):
    message: str
    history: list[Turn] = []


class ClassifyResponse(BaseModel):
    is_learning_context: bool
    requests_complete_answer: bool
    has_self_attempt_evidence: bool
    uncertain: bool
    confidence: float


@app.post("/classify", response_model=ClassifyResponse)
def classify_endpoint(req: ClassifyRequest) -> dict:
    return classify(req.message, [t.model_dump() for t in req.history])
