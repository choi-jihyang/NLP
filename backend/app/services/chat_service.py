"""학생 메시지 한 건을 처리하는 흐름: 분류 → 정책 → 프롬프트 → LLM → 누출 검사.

사용량 확인과 대화 저장은 DB 모델이 생기면 이 앞뒤에 붙는다.
"""

from dataclasses import dataclass

from app.classifier.base import ClassificationResult, Classifier
from app.leak_guard.base import LeakGuard
from app.llm.base import LLMProvider
from app.schemas.chat import ChatTurn
from app.services import policy, prompt_builder


@dataclass(frozen=True)
class ChatReply:
    text: str
    mode: policy.ResponseMode
    classification: ClassificationResult
    used_llm: bool
    leak_blocked: bool = False
    """누출 검사가 LLM 답변을 막았는가 (막히면 text는 LEAK_BLOCKED_REPLY)"""
    blocked_draft: str | None = None
    """막힌 LLM 답변 원문. 교수자 기록·시연용이며 학생에게 보내지 않는다"""
    leak_reasons: tuple[str, ...] = ()


async def reply(
    message: str,
    history: list[ChatTurn],
    base_prompt: str,
    classifier: Classifier,
    llm: LLMProvider,
    leak_guard: LeakGuard,
    min_confidence: float = 0.5,
    choice: policy.HelpChoice | None = None,
    context: prompt_builder.PromptContext | None = None,
) -> ChatReply:
    """`context`가 있으면 build_from_config로, 없으면 base_prompt로 시스템 프롬프트를 만든다."""
    result = await classifier.classify(message, history)
    decision = policy.decide(result, min_confidence, choice)

    if decision.fixed_reply is not None:
        return ChatReply(decision.fixed_reply, decision.mode, result, used_llm=False)

    if context is not None:
        system = prompt_builder.build_from_config(context, decision.directive)
    else:
        system = prompt_builder.compose(base_prompt, decision.directive)
    draft = await llm.generate(system, [*history, ChatTurn(role="student", content=message)])
    if not draft.strip():
        # 생각 태그만 내거나 빈 답을 내면 학생에게 빈 말풍선 대신 시도를 묻는 고정 문구를 보낸다
        return ChatReply(policy.ASK_ATTEMPT_REPLY, decision.mode, result, used_llm=True)

    # 마지막 필터: 프롬프트가 뚫려도 정답·완성 코드는 학생에게 가지 않는다 (모든 LLM 모드에 적용)
    check = await leak_guard.check(draft, history)
    if check.leaked:
        return ChatReply(
            policy.LEAK_BLOCKED_REPLY, decision.mode, result, used_llm=True,
            leak_blocked=True, blocked_draft=draft, leak_reasons=tuple(check.reasons),
        )
    return ChatReply(draft, decision.mode, result, used_llm=True)
