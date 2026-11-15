"""분류기 인터페이스. NLP 팀과의 계약은 nlp/CONTRACT.md 와 같아야 한다."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.schemas.chat import ChatTurn


class ClassificationResult(BaseModel):
    is_learning_context: bool
    """과제·학습과 관련된 대화인가"""
    requests_complete_answer: bool
    """정답·전체 풀이·완성 코드를 통째로 요구하는가"""
    has_self_attempt_evidence: bool
    """학생이 직접 시도한 흔적(식, 중간 결과, 작성한 코드 등)이 메시지·대화에 있는가"""
    uncertain: bool
    """분류기 스스로 판단이 모호하다고 보는가"""
    confidence: float = Field(ge=0.0, le=1.0)
    """판단 전체에 대한 확신도"""


class Classifier(ABC):
    @abstractmethod
    async def classify(self, message: str, history: list[ChatTurn]) -> ClassificationResult:
        """학생의 새 메시지와 이전 대화(오래된 순)를 받아 분류한다."""
