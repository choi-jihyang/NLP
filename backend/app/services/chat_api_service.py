"""학생 채팅 API · 붙여넣기 기록 (⑥, chat-policy.md 처리 순서).

1. 잠김 확인            최종 제출 후 ALREADY_SUBMITTED · 개념 확인 중 · AI 끈 간단 제작 FORBIDDEN
2. 사용량 확인          학생 메시지 수 ≥ usage_limit → USAGE_LIMIT, LLM 호출 안 함(I6)
3. chat_service.reply   분류 → 정책(OFFER_CHOICES · 고른 뒤 HINT_ONLY) → 프롬프트 → LLM → 누출 검사
4. 저장                 학생 메시지(🔒 분류 결과) · AI 답(🔒 누출 검사), 힌트 단계

도움 방식 고르기: 학생이 choice를 보내면 직전 AI 답이 OFFER_CHOICES여야 하고, 그때 분류는
OFFER_CHOICES를 부른 원래 학생 메시지로 다시 한다(빈 메시지를 분류하지 않음). 무엇을 골라도 HINT_ONLY(I1).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.classifier.base import Classifier
from app.core.config import get_settings
from app.core.enums import AnswerStatus, ChatRole, QuestionType
from app.core.errors import AppError, ErrorCode
from app.leak_guard.base import LeakGuard
from app.llm.base import LLMProvider
from app.models import Answer, Assignment, ChatMessage, PasteEvent, Question, Submission, User
from app.schemas.ai_policy import AiPolicy
from app.schemas.assignments import AnswerKey
from app.schemas.chat import ChatState, ChatTrace, ChatTurn, ChatTurnOut, PasteBody
from app.schemas.student_assignments import MAX_HINT_STEPS
from app.services import chat_service
from app.services.policy import USAGE_LIMIT_REPLY, HelpChoice, ResponseMode
from app.services.prompt_builder import PromptContext
from app.services.simulate_service import classification_label
from app.services.submission_service import _answer, _context, _question

_HINT_MODES = (ResponseMode.HINT_ONLY, ResponseMode.NEXT_STEP)


# ---------- 맥락 ----------


def prompt_context(assignment: Assignment, q: Question) -> PromptContext:
    key = AnswerKey.model_validate(q.answer_key)
    secrets = [v for v in (key.answer, key.model_answer) if v]
    mc_index = int(key.answer) if key.answer and key.answer.isdigit() else -1
    if q.type is QuestionType.MULTIPLE_CHOICE and 0 <= mc_index < len(q.choices):
        secrets = [f"정답 선택지: {mc_index + 1}번 {q.choices[mc_index]}"]
    secrets += key.accepted_answers + [t.expected_output for t in key.hidden_tests]
    description = "\n\n".join(x for x in (assignment.description, f"[이 문항]\n{q.prompt}", q.code) if x and x.strip())
    return PromptContext(policy=AiPolicy.model_validate(assignment.policy), description=description,
                         protected_values=secrets, language=assignment.language)


def _messages(db: Session, answer: Answer) -> list[ChatMessage]:
    query = select(ChatMessage).where(ChatMessage.answer_id == answer.seq)
    return list(db.scalars(query.order_by(ChatMessage.created_at, ChatMessage.seq)))


def _student_count(db: Session, sub: Submission) -> int:
    """사용량: 이 제출(과제)의 모든 문항에서 학생이 보낸 메시지 수 (schema "사용량 상한")."""
    query = (
        select(func.count()).select_from(ChatMessage).join(Answer, ChatMessage.answer_id == Answer.seq)
        .where(Answer.submission_id == sub.seq, ChatMessage.role == ChatRole.STUDENT)
    )
    return db.scalar(query) or 0


def _trace(student: ChatMessage | None, assistant: ChatMessage) -> ChatTrace | None:
    if not get_settings().demo_trace or student is None or student.uncertain is None:
        return None
    from app.classifier.base import ClassificationResult

    result = ClassificationResult(
        is_learning_context=bool(student.is_learning_context),
        requests_complete_answer=bool(student.requests_complete_answer),
        has_self_attempt_evidence=bool(student.has_self_attempt_evidence),
        uncertain=bool(student.uncertain), confidence=student.confidence or 0.0,
    )
    return ChatTrace(classification=classification_label(result), attempt=result.has_self_attempt_evidence,
                     leak_blocked=bool(assistant.leak_blocked), blocked_draft=assistant.blocked_draft)


def _state(db: Session, assignment: Assignment, sub: Submission, answer: Answer | None, question_id: int) -> ChatState:
    policy = AiPolicy.model_validate(assignment.policy)
    turns: list[ChatTurnOut] = []
    last_student: ChatMessage | None = None
    for m in _messages(db, answer) if answer else []:
        if m.role is ChatRole.STUDENT:
            last_student = m
            turns.append(ChatTurnOut(role=m.role, text=m.content, response_mode=None))
        else:
            turns.append(ChatTurnOut(role=m.role, text=m.content, response_mode=m.response_mode,
                                     trace=_trace(last_student, m)))
    return ChatState(
        question_id=question_id, turns=turns, hint_step=answer.hint_step if answer else 0,
        max_hint_steps=MAX_HINT_STEPS[policy.hint_mode],
        usage_remaining=max(policy.usage_limit - _student_count(db, sub), 0),
    )


def _check_unlocked(sub: Submission, q: Question, answer: Answer) -> None:
    if sub.finalized_at is not None:
        raise AppError(ErrorCode.ALREADY_SUBMITTED)
    if q.type is QuestionType.PROJECT and not q.ai_help:
        raise AppError(ErrorCode.FORBIDDEN, "이 문항은 AI 도움을 쓰지 않아요.")
    if answer.status is AnswerStatus.AWAITING_CHECK:
        raise AppError(ErrorCode.FORBIDDEN, "개념 확인 중에는 AI 도움을 쓸 수 없어요.")


# ---------- API ----------


def get_chat(db: Session, student: User, assignment_id: int, question_id: int) -> ChatState:
    assignment, sub = _context(db, student, assignment_id)
    q = _question(db, assignment, question_id)
    answer = db.scalar(select(Answer).where(Answer.submission_id == sub.seq, Answer.question_id == q.seq))
    db.commit()
    return _state(db, assignment, sub, answer, q.seq)


async def send_chat(
    db: Session, student: User, assignment_id: int, question_id: int, message: str, choice: HelpChoice | None,
    classifier: Classifier, llm: LLMProvider, leak_guard: LeakGuard,
) -> ChatState:
    assignment, sub = _context(db, student, assignment_id)
    q = _question(db, assignment, question_id)
    answer = _answer(db, sub, q)
    _check_unlocked(sub, q, answer)
    policy = AiPolicy.model_validate(assignment.policy)
    settings = get_settings()

    if choice is None and not message.strip():
        raise AppError(ErrorCode.VALIDATION_FAILED, "메시지를 입력해 주세요.")
    earlier = _messages(db, answer)
    text_for_classifier, history_msgs = message, earlier
    if choice is not None:
        last_ai = next((m for m in reversed(earlier) if m.role is ChatRole.ASSISTANT), None)
        if last_ai is None or last_ai.response_mode is not ResponseMode.OFFER_CHOICES:
            raise AppError(ErrorCode.CONFLICT, "도움 방식을 고를 차례가 아니에요.")
        origin = next((m for m in reversed(earlier) if m.role is ChatRole.STUDENT and m.help_choice is None), None)
        if origin is None:
            raise AppError(ErrorCode.CONFLICT, "도움 방식을 고를 차례가 아니에요.")
        text_for_classifier = origin.content
        history_msgs = earlier[: earlier.index(origin)]

    student_msg = ChatMessage(answer_id=answer.seq, role=ChatRole.STUDENT, content=message, help_choice=choice)

    # I6: 상한이면 분류기 · LLM 모두 부르지 않는다
    if _student_count(db, sub) >= policy.usage_limit:
        db.add(student_msg)
        db.add(ChatMessage(answer_id=answer.seq, role=ChatRole.ASSISTANT, content=USAGE_LIMIT_REPLY,
                           response_mode=ResponseMode.USAGE_LIMIT, hint_step=answer.hint_step))
        db.commit()
        return _state(db, assignment, sub, answer, q.seq)

    history = [
        ChatTurn(role="student" if m.role is ChatRole.STUDENT else "assistant", content=m.content)
        for m in history_msgs if m.content.strip()
    ][-settings.chat_history_turns:]
    out = await chat_service.reply(
        text_for_classifier, history, "", classifier, llm, leak_guard, settings.classifier_min_confidence,
        choice=choice, context=prompt_context(assignment, q),
    )

    c = out.classification
    student_msg.is_learning_context = c.is_learning_context
    student_msg.requests_complete_answer = c.requests_complete_answer
    student_msg.has_self_attempt_evidence = c.has_self_attempt_evidence
    student_msg.uncertain, student_msg.confidence = c.uncertain, c.confidence
    db.add(student_msg)
    if out.mode in _HINT_MODES and out.used_llm and not out.leak_blocked:
        answer.hint_step = min(answer.hint_step + 1, MAX_HINT_STEPS[policy.hint_mode])
    db.add(ChatMessage(
        answer_id=answer.seq, role=ChatRole.ASSISTANT, content=out.text, response_mode=out.mode,
        hint_step=answer.hint_step, leak_blocked=out.leak_blocked if out.used_llm else None,
        blocked_draft=out.blocked_draft,
    ))
    db.commit()
    return _state(db, assignment, sub, answer, q.seq)


def log_paste(db: Session, student: User, body: PasteBody) -> None:
    """이 학생의 그 문항 답에 묶어 저장(답이 없으면 만든다). 내용은 받지도 저장하지도 않는다(I5)."""
    q = db.get(Question, body.question_id)
    if q is None:
        raise AppError(ErrorCode.NOT_FOUND)
    assignment, sub = _context(db, student, q.assignment_id)
    answer = _answer(db, sub, _question(db, assignment, q.seq))
    db.add(PasteEvent(answer_id=answer.seq, field=body.field, length=body.length, pasted_at=body.pasted_at))
    db.commit()
