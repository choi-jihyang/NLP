"""분류 결과 → AI 응답 정책 분기."""

from dataclasses import dataclass
from enum import StrEnum

from app.classifier.base import ClassificationResult

ASK_ATTEMPT_REPLY = "이미 시도한 부분이 있나요? 어디까지 풀어 봤는지 적어 주면 그다음 단계를 함께 생각해 볼게요."
OFF_TOPIC_REPLY = "지금은 과제와 관련된 질문에만 도움을 줄 수 있어요. 문항에서 막힌 부분을 알려 주세요."


class ResponseMode(StrEnum):
    NEXT_STEP = "next_step"
    """일반 학습 도움: 설정된 단계 안내 정책대로 응답"""
    HINT_ONLY = "hint_only"
    """완성 답안 요청 + 시도 근거 없음: 힌트 위주로만 응답"""
    ASK_ATTEMPT = "ask_attempt"
    """판단이 모호함: LLM 호출 없이 시도 여부를 되묻는다"""
    OFF_TOPIC = "off_topic"
    """학습과 무관한 대화: LLM 호출 없이 과제로 돌려보낸다"""


@dataclass(frozen=True)
class PolicyDecision:
    mode: ResponseMode
    directive: str | None = None
    """LLM을 호출할 때 시스템 프롬프트 끝에 덧붙일 지시. fixed_reply가 있으면 None"""
    fixed_reply: str | None = None
    """LLM을 호출하지 않고 그대로 보낼 답변"""


_HINT_ONLY_DIRECTIVE = (
    "[이번 응답 정책: 힌트만]\n"
    "학생이 완성된 답이나 전체 풀이를 요청했지만 스스로 시도한 근거가 없다. "
    "정답·최종 값·완성 코드·전체 풀이는 절대 주지 않는다. "
    "문제를 푸는 데 필요한 개념이나 첫 단계에 대한 힌트 하나만 주고, 학생이 직접 시도해 보도록 권한다."
)
_NEXT_STEP_DIRECTIVE = (
    "[이번 응답 정책: 다음 단계 안내]\n"
    "학생이 실제로 보여 준 풀이까지만 근거로 삼아, 그다음 한 단계만 안내한다."
)


def decide(result: ClassificationResult, min_confidence: float = 0.5) -> PolicyDecision:
    """분류 결과에 따라 응답 방식을 정한다.

    우선순위: 모호함 → 학습 외 대화 → 완성 답안 요청(시도 없음) → 일반 안내
    """
    if result.uncertain or result.confidence < min_confidence:
        return PolicyDecision(ResponseMode.ASK_ATTEMPT, fixed_reply=ASK_ATTEMPT_REPLY)
    if not result.is_learning_context:
        return PolicyDecision(ResponseMode.OFF_TOPIC, fixed_reply=OFF_TOPIC_REPLY)
    if result.requests_complete_answer and not result.has_self_attempt_evidence:
        return PolicyDecision(ResponseMode.HINT_ONLY, directive=_HINT_ONLY_DIRECTIVE)
    return PolicyDecision(ResponseMode.NEXT_STEP, directive=_NEXT_STEP_DIRECTIVE)
