"""학생 풀이 · 제출 (api-contract "풀이 · 제출", schema submissions · answers · concept_check_items).

- 공개 테스트 실행(/run)은 공개 테스트만 돌리고 결과를 그대로 보여 준다.
- 문항 제출 때 자동 채점한다(객관식 · 출력 예측 · 코드 작성 숨김 테스트 포함). 결과는 🔒 컬럼에만 저장하고
  결과 공개 전까지 학생 응답에 넣지 않는다(AnswerState에 필드 자체가 없음).
- 힌트 없이 처음 낸 문항은 개념 확인(AWAITING_CHECK)을 거친다. 질문은 지금은 유형별 고정 문구,
  AI 작성 점수는 NLP 담당이 정해지면 붙인다(scope ②) — 그 전에는 추가 질문이 생기지 않는다.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.enums import AnswerStatus, HintPenalty, Language, QuestionType
from app.core.errors import AppError, ErrorCode
from app.models import Answer, Assignment, ConceptCheckItem, Question, Submission, User
from app.runner import CodeRunner, IOCase, RunnerUnavailableError
from app.schemas.ai_policy import AiPolicy
from app.schemas.assignments import AnswerKey
from app.schemas.submissions import (
    AnswerState,
    ConceptCheckState,
    PublicTestResult,
    RunOut,
    SubmissionOut,
)
from app.services.access import active_enrollment
from app.services.assignment_service import questions_of
from app.services.student_assignment_service import published_for_student

CONCEPT_QUESTION: dict[QuestionType, str] = {
    QuestionType.MULTIPLE_CHOICE: "이 답을 고른 이유를 한두 문장으로 설명해 주세요.",
    QuestionType.SHORT_ANSWER: "이 출력이 나오는 이유를 코드가 실행되는 순서대로 설명해 주세요.",
    QuestionType.CODE: "제출한 코드에서 가장 중요한 줄 하나를 골라, 그 줄이 무엇을 하는지 자기 말로 설명해 주세요.",
    QuestionType.PROJECT: "제출한 코드의 전체 흐름을 두세 문장으로 설명해 주세요. 어떤 방식을 골랐는지도 적어 주세요.",
}
FOLLOW_UP_THRESHOLD = 0.7
"""AI 작성 점수가 이 이상이면 질문을 하나 더 한다(점수가 생기면 사용)"""


# ---------- 조회 · 권한 ----------


def _context(db: Session, student: User, assignment_id: int) -> tuple[Assignment, Submission]:
    assignment = published_for_student(db, student, assignment_id)
    enrollment = active_enrollment(db, student, assignment.class_id)
    sub = db.scalar(select(Submission).where(
        Submission.assignment_id == assignment.seq, Submission.enrollment_id == enrollment.seq
    ))
    if sub is None:
        where = (Submission.assignment_id == assignment.seq, Submission.enrollment_id == enrollment.seq)
        new = Submission(assignment_id=assignment.seq, enrollment_id=enrollment.seq)
        sub = _create_once(db, new, lambda: db.scalar(select(Submission).where(*where)))
    return assignment, sub


def _question(db: Session, assignment: Assignment, question_id: int) -> Question:
    q = db.get(Question, question_id)
    if q is None or q.assignment_id != assignment.seq:
        raise AppError(ErrorCode.NOT_FOUND)
    return q


def _create_once(db: Session, row, find):  # noqa: ANN001, ANN202
    """처음 활동할 때 행을 만든다. 같은 순간 들어온 다른 요청이 먼저 만들었으면(UNIQUE) 그 행을 쓴다.

    화면은 과제를 열 때 제출 · 채팅 요청을 동시에 보내므로 경쟁이 실제로 난다(11/26 화면 연결 때 500 발견).
    """
    try:
        with db.begin_nested():
            db.add(row)
            db.flush()
        return row
    except IntegrityError:
        existing = find()
        if existing is None:
            raise
        return existing


def _answer(db: Session, sub: Submission, q: Question) -> Answer:
    def find() -> Answer | None:
        return db.scalar(select(Answer).where(Answer.submission_id == sub.seq, Answer.question_id == q.seq))

    a = find()
    if a is None:
        a = _create_once(db, Answer(submission_id=sub.seq, question_id=q.seq), find)
    return a


def _items(db: Session, answer: Answer) -> list[ConceptCheckItem]:
    query = select(ConceptCheckItem).where(ConceptCheckItem.answer_id == answer.seq)
    return list(db.scalars(query.order_by(ConceptCheckItem.position)))


def _ensure_open(assignment: Assignment, sub: Submission) -> None:
    """최종 제출 뒤 → ALREADY_SUBMITTED, 마감 뒤 → CONFLICT (api-contract 결정 C)."""
    if sub.finalized_at is not None:
        raise AppError(ErrorCode.ALREADY_SUBMITTED)
    if assignment.due_at is not None and now_kst() > assignment.due_at:
        raise AppError(ErrorCode.CONFLICT, "마감이 지나 제출할 수 없습니다.")


def _state(db: Session, answer: Answer) -> AnswerState:
    items = _items(db, answer)
    check = None
    if items:
        check = ConceptCheckState(
            questions=[i.question_text for i in items], answered=sum(i.reply is not None for i in items)
        )
    return AnswerState(
        question_id=answer.question_id, content=answer.content, status=answer.status,
        submitted_at=answer.submitted_at, submit_count=answer.submit_count, hint_step=answer.hint_step,
        concept_check=check,
    )


def submission_out(db: Session, assignment: Assignment, sub: Submission) -> SubmissionOut:
    answers = db.scalars(select(Answer).where(Answer.submission_id == sub.seq))
    return SubmissionOut(
        assignment_id=assignment.seq, answers={a.question_id: _state(db, a) for a in answers},
        finalized=sub.finalized_at is not None, results_released=assignment.results_released_at is not None,
    )


def get_submission(db: Session, student: User, assignment_id: int) -> SubmissionOut:
    assignment, sub = _context(db, student, assignment_id)
    db.commit()
    return submission_out(db, assignment, sub)


# ---------- 공개 테스트 실행 ----------


async def run_public(
    db: Session, student: User, assignment_id: int, question_id: int, code: str, runner: CodeRunner
) -> RunOut:
    assignment, sub = _context(db, student, assignment_id)
    q = _question(db, assignment, question_id)
    db.commit()
    if sub.finalized_at is not None:
        raise AppError(ErrorCode.ALREADY_SUBMITTED)
    if q.type is not QuestionType.CODE:
        raise AppError(ErrorCode.CONFLICT, "코드 작성 문항만 테스트를 실행할 수 있습니다.")
    tests = [IOCase(**t) for t in q.public_tests]  # 숨김 테스트는 여기서 쓰지 않는다
    try:
        result = await runner.run(assignment.language, code, tests)
    except RunnerUnavailableError as exc:
        raise AppError(ErrorCode.RUNNER_UNAVAILABLE) from exc
    return RunOut(ok=result.ok, error=result.error, results=[
        PublicTestResult(input=t.input, expected_output=t.expected_output, actual_output=r.actual_output,
                         passed=r.passed, error=r.error)
        for t, r in zip(tests, result.results, strict=True)
    ])


# ---------- 채점 ----------


def _norm(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().replace("\r\n", "\n").split("\n"))


def _penalized(points: int, hint_step: int, policy: AiPolicy) -> int:
    if policy.hint_penalty is HintPenalty.PRACTICE and hint_step > 0:
        return 0
    if policy.hint_penalty is HintPenalty.PER_STEP:
        return max(points - hint_step, 0)
    return points


async def grade(q: Question, answer: Answer, policy: AiPolicy, language: Language, runner: CodeRunner) -> None:
    """🔒 is_correct · test_results · score를 채운다. 간단 제작은 교수자 채점이라 비워 둔다."""
    key = AnswerKey.model_validate(q.answer_key)
    content = answer.content
    if q.type is QuestionType.PROJECT:
        answer.is_correct, answer.test_results = None, None
        return
    if q.type is QuestionType.MULTIPLE_CHOICE:
        answer.is_correct = content.strip() == (key.answer or "")
        earned = q.points if answer.is_correct else 0
    elif q.type is QuestionType.SHORT_ANSWER:
        accepted = {_norm(x) for x in [key.answer or "", *key.accepted_answers] if x}
        answer.is_correct = _norm(content) in accepted
        earned = q.points if answer.is_correct else 0
    else:  # CODE: 공개 + 숨김 테스트 전부
        tests = [IOCase(**t) for t in q.public_tests] + [IOCase(**t.model_dump()) for t in key.hidden_tests]
        try:
            result = await runner.run(language, content, tests)
        except RunnerUnavailableError as exc:
            raise AppError(ErrorCode.RUNNER_UNAVAILABLE) from exc
        hidden_from = len(q.public_tests)
        answer.test_results = [
            {**r.model_dump(), "hidden": i >= hidden_from} for i, r in enumerate(result.results)
        ]
        passed = sum(r.passed for r in result.results)
        answer.is_correct = bool(tests) and passed == len(tests)
        earned = q.points * passed // len(tests) if tests else 0  # 통과한 테스트 비율만큼(내림)
    answer.score = _penalized(earned, answer.hint_step, policy)


# ---------- 문항 제출 · 개념 확인 · 최종 제출 ----------


async def submit_answer(
    db: Session, student: User, assignment_id: int, question_id: int, content: str, runner: CodeRunner
) -> SubmissionOut:
    assignment, sub = _context(db, student, assignment_id)
    _ensure_open(assignment, sub)
    q = _question(db, assignment, question_id)
    policy = AiPolicy.model_validate(assignment.policy)
    answer = _answer(db, sub, q)
    if q.type is QuestionType.MULTIPLE_CHOICE and not (content.isdigit() and int(content) < len(q.choices)):
        raise AppError(ErrorCode.VALIDATION_FAILED, "선택지 번호('0'부터)를 보내야 합니다.")

    first_solo = answer.submit_count == 0 and answer.hint_step == 0
    answer.content = content
    await grade(q, answer, policy, assignment.language, runner)  # 실행기가 없으면 여기서 503, 저장 안 함
    answer.submit_count += 1
    answer.submitted_at = now_kst()

    items = _items(db, answer)
    pending = any(i.reply is None for i in items)
    if policy.concept_check_enabled and (pending or (first_solo and not items)):
        if not items:
            db.add(ConceptCheckItem(answer_id=answer.seq, position=0, question_text=CONCEPT_QUESTION[q.type]))
        answer.status = AnswerStatus.AWAITING_CHECK
    else:
        answer.status = AnswerStatus.SUBMITTED
    db.commit()
    return submission_out(db, assignment, sub)


def answer_concept_check(
    db: Session, student: User, assignment_id: int, question_id: int, reply: str, elapsed_ms: int
) -> SubmissionOut:
    assignment, sub = _context(db, student, assignment_id)
    _ensure_open(assignment, sub)
    answer = _answer(db, sub, _question(db, assignment, question_id))
    item = next((i for i in _items(db, answer) if i.reply is None), None)
    if answer.status is not AnswerStatus.AWAITING_CHECK or item is None:
        raise AppError(ErrorCode.CONFLICT, "개념 확인을 기다리는 문항이 아닙니다.")
    item.reply, item.elapsed_ms, item.answered_at = reply, elapsed_ms, now_kst()
    # AI 작성 점수(NLP, scope ②)가 생기면: item.ai_written_score를 채우고 높으면 position 1 질문을 추가한다
    needs_follow_up = (
        item.position == 0 and item.ai_written_score is not None and item.ai_written_score >= FOLLOW_UP_THRESHOLD
    )
    if needs_follow_up:
        follow_up = "방금 설명한 부분을 바꾸면 결과가 어떻게 달라질지 한 가지 예로 말해 주세요."
        db.add(ConceptCheckItem(answer_id=answer.seq, position=1, question_text=follow_up))
    else:
        answer.status = AnswerStatus.SUBMITTED
    db.commit()
    return submission_out(db, assignment, sub)


def cancel_concept_check(db: Session, student: User, assignment_id: int, question_id: int) -> SubmissionOut:
    """답 고치러 돌아가기 → DRAFT. 추가 질문 단계(이미 하나 답함)에서는 CONFLICT."""
    assignment, sub = _context(db, student, assignment_id)
    _ensure_open(assignment, sub)
    answer = _answer(db, sub, _question(db, assignment, question_id))
    items = _items(db, answer)
    if answer.status is not AnswerStatus.AWAITING_CHECK:
        raise AppError(ErrorCode.CONFLICT, "개념 확인을 기다리는 문항이 아닙니다.")
    if any(i.reply is not None for i in items):
        raise AppError(ErrorCode.CONFLICT, "추가 질문 단계에서는 돌아갈 수 없습니다.")
    answer.status = AnswerStatus.DRAFT
    db.commit()
    return submission_out(db, assignment, sub)


def finalize(db: Session, student: User, assignment_id: int) -> SubmissionOut:
    assignment, sub = _context(db, student, assignment_id)
    _ensure_open(assignment, sub)
    submitted = {
        a.question_id for a in db.scalars(select(Answer).where(Answer.submission_id == sub.seq))
        if a.status is AnswerStatus.SUBMITTED
    }
    missing = [i for i, q in enumerate(questions_of(db, assignment.seq), start=1) if q.seq not in submitted]
    if missing:
        raise AppError(ErrorCode.CONFLICT, f"아직 내지 않은 문항이 있습니다: {', '.join(map(str, missing))}번")
    sub.finalized_at = now_kst()
    db.commit()
    return submission_out(db, assignment, sub)
