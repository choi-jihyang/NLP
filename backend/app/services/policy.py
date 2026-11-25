"""분류 결과 → AI 응답 정책 분기."""

from dataclasses import dataclass
from enum import StrEnum

from app.classifier.base import ClassificationResult

OFFER_CHOICES_REPLY = "완성된 답을 바로 받기보다, 아래에서 골라 볼래요?"
"""완성 답안 요청 + 시도 근거 없음: LLM 없이 도움 방식을 고르게 한다 (api-contract 채팅)"""
USAGE_LIMIT_REPLY = "이 과제에서 쓸 수 있는 AI 도움 횟수를 모두 썼어요. 지금까지 받은 힌트로 직접 풀어 보세요."
ASK_ATTEMPT_REPLY = "이미 시도한 부분이 있나요? 어디까지 풀어 봤는지 적어 주면 그다음 단계를 함께 생각해 볼게요."
OFF_TOPIC_REPLY = "지금은 과제와 관련된 질문에만 도움을 줄 수 있어요. 문항에서 막힌 부분을 알려 주세요."
LEAK_BLOCKED_REPLY = (
    "이 답변에는 정답이나 완성 코드가 들어 있어서 보여 드릴 수 없어요. "
    "직접 써 본 코드나 막힌 줄을 알려 주면 그다음 한 단계를 함께 생각해 볼게요."
)
"""누출 검사가 LLM 답변을 막았을 때 대신 보내는 답변"""


class ResponseMode(StrEnum):
    """DB·API에는 대문자 문자열로 나간다 (schema.md Enum, api-contract 결정 B)."""

    NEXT_STEP = "NEXT_STEP"
    """일반 학습 도움: 설정된 단계 안내 정책대로 응답"""
    HINT_ONLY = "HINT_ONLY"
    """완성 답안 요청 + 시도 근거 없음 + 도움 방식을 고름: 힌트 위주로만 응답"""
    ASK_ATTEMPT = "ASK_ATTEMPT"
    """판단이 모호함: LLM 호출 없이 시도 여부를 되묻는다"""
    OFF_TOPIC = "OFF_TOPIC"
    """학습과 무관한 대화: LLM 호출 없이 과제로 돌려보낸다"""
    USAGE_LIMIT = "USAGE_LIMIT"
    """사용량 상한: LLM 호출 없이 안내 (I6). 판단은 채팅 service가 분류 전에 한다"""
    OFFER_CHOICES = "OFFER_CHOICES"
    """완성 답안 요청 + 시도 근거 없음 + 아직 고르지 않음: LLM 없이 도움 방식 고르기"""


class HelpChoice(StrEnum):
    """OFFER_CHOICES 뒤 학생이 고르는 도움 방식. 어느 것을 골라도 정책은 HINT_ONLY (I1)."""

    FIRST_HINT = "FIRST_HINT"
    FEEDBACK = "FEEDBACK"
    ORIGINAL = "ORIGINAL"


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
_CHOICE_DIRECTIVES: dict[HelpChoice, str] = {
    HelpChoice.FIRST_HINT: "학생은 '첫 힌트 받기'를 골랐다. 문제를 시작하는 데 필요한 첫 힌트 하나만 준다.",
    HelpChoice.FEEDBACK: (
        "학생은 '내 생각 확인받기'를 골랐다. 학생에게 지금 생각한 방법을 한두 문장으로 적어 달라고 요청하고, "
        "적은 내용이 있으면 그 내용에 대해서만 짧게 피드백한다."
    ),
    HelpChoice.ORIGINAL: (
        "학생은 '원래 요청대로'를 골랐다. 그래도 완성 답·완성 코드는 주지 않는다. "
        "왜 바로 줄 수 없는지 한 문장으로 말하고 힌트 하나만 준다."
    ),
}
_NEXT_STEP_DIRECTIVE = (
    "[이번 응답 정책: 다음 단계 안내]\n"
    "학생이 실제로 보여 준 풀이까지만 근거로 삼아, 그다음 한 단계만 안내한다."
)


def decide(
    result: ClassificationResult, min_confidence: float = 0.5, choice: HelpChoice | None = None
) -> PolicyDecision:
    """분류 결과에 따라 응답 방식을 정한다.

    우선순위: 모호함 → 학습 외 대화 → 완성 답안 요청(시도 없음) → 일반 안내
    완성 답안 요청 + 시도 없음: 아직 안 골랐으면 OFFER_CHOICES(LLM 없음), 골랐으면 무엇이든 HINT_ONLY (I1).
    `choice`는 그 경우에만 쓰인다. 다른 분기에서는 무시한다.
    """
    if result.uncertain or result.confidence < min_confidence:
        return PolicyDecision(ResponseMode.ASK_ATTEMPT, fixed_reply=ASK_ATTEMPT_REPLY)
    if not result.is_learning_context:
        return PolicyDecision(ResponseMode.OFF_TOPIC, fixed_reply=OFF_TOPIC_REPLY)
    if result.requests_complete_answer and not result.has_self_attempt_evidence:
        if choice is None:
            return PolicyDecision(ResponseMode.OFFER_CHOICES, fixed_reply=OFFER_CHOICES_REPLY)
        return PolicyDecision(
            ResponseMode.HINT_ONLY, directive=f"{_HINT_ONLY_DIRECTIVE}\n{_CHOICE_DIRECTIVES[choice]}"
        )
    return PolicyDecision(ResponseMode.NEXT_STEP, directive=_NEXT_STEP_DIRECTIVE)
