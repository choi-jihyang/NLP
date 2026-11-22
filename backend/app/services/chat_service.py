"""학생 메시지 한 건을 처리하는 흐름: 분류 → 정책 → 프롬프트 → LLM.

사용량 확인과 대화 저장은 DB 모델이 생기면 이 앞뒤에 붙는다.
"""

from dataclasses import dataclass

from app.classifier.base import ClassificationResult, Classifier
from app.llm.base import LLMProvider
from app.schemas.chat import ChatTurn
from app.services import policy, prompt_builder


@dataclass(frozen=True)
class ChatReply:
    text: str
    mode: policy.ResponseMode
    classification: ClassificationResult
    used_llm: bool


async def reply(
    message: str,
    history: list[ChatTurn],
    base_prompt: str,
    classifier: Classifier,
    llm: LLMProvider,
    min_confidence: float = 0.5,
) -> ChatReply:
    result = await classifier.classify(message, history)
    decision = policy.decide(result, min_confidence)

    if decision.fixed_reply is not None:
        return ChatReply(decision.fixed_reply, decision.mode, result, used_llm=False)

    system = prompt_builder.compose(base_prompt, decision.directive)
    text = await llm.generate(system, [*history, ChatTurn(role="student", content=message)])
    if not text.strip():
        # 생각 태그만 내거나 빈 답을 내면 학생에게 빈 말풍선 대신 시도를 묻는 고정 문구를 보낸다
        text = policy.ASK_ATTEMPT_REPLY
    return ChatReply(text, decision.mode, result, used_llm=True)
