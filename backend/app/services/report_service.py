"""이해 확인 · 교수자 반 리포트 · 학생별 기록 · 내 리포트.

숫자는 저장된 기록(answers · understanding_answers · concept_check_items · chat_messages · paste_events)으로 계산하고,
문장 칸은 과제 파일의 오개념 표 · 확인 문제 결과로 만든 규칙 기반 문장이다(LLM 아님).
결과 공개 전 학생에게는 정오 · 점수 · 정답을 보내지 않는다(내 리포트는 released=false만).
"""

from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.enums import AnswerStatus, ChatRole, ConceptStatus, Confidence, QuestionType
from app.core.errors import AppError, ErrorCode
from app.models import (
    Answer,
    Assignment,
    ChatMessage,
    ConceptCheckItem,
    Enrollment,
    PasteEvent,
    Question,
    Submission,
    UnderstandingAnswer,
    UnderstandingCheck,
    User,
)
from app.schemas.ai_policy import AiPolicy
from app.schemas.assignments import AnswerKey, Variant
from app.schemas.reports import (
    AssignmentReport,
    CheckItem,
    CheckReceipt,
    CheckSubmission,
    ConceptRow,
    DependencyRow,
    MistakeRow,
    MyQuestionResult,
    MyReport,
    MyReportPending,
    QuestionMistakes,
    QuestionStat,
    RecordConversation,
    RecordRow,
    RecordTurn,
    SignalRow,
    StudentRecord,
    Supplement,
    UnderstandingCheckOut,
)
from app.services.access import approved_count
from app.services.assignment_service import get_owned, questions_of
from app.services.grading_service import signals as paste_signals
from app.services.policy_text import TYPE_LABEL
from app.services.submission_service import _context, _norm

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"


def _pct(part: int, whole: int) -> int:
    return round(100 * part / whole) if whole else 0


def _choice_label(q: Question, index: str) -> str:
    i = int(index) if index.isdigit() else -1
    if 0 <= i < len(q.choices):
        mark = CIRCLED[i] if i < len(CIRCLED) else f"{i + 1}."
        return f"{mark} {q.choices[i]}"
    return index


def variant_correct(v: Variant, value: str) -> bool:
    if v.type is QuestionType.MULTIPLE_CHOICE:
        return value.strip() == v.answer
    return _norm(value) in {_norm(x) for x in [v.answer, *v.accepted_answers] if x}


# ---------- 데이터 한 번에 읽기 ----------


@dataclass
class StudentData:
    enrollment: Enrollment
    sub: Submission
    answers: dict[int, Answer] = field(default_factory=dict)  # question seq → answer
    checks: dict[int, UnderstandingAnswer] = field(default_factory=dict)
    concept: dict[int, list[ConceptCheckItem]] = field(default_factory=dict)  # answer seq → items
    pastes: dict[int, list[PasteEvent]] = field(default_factory=dict)  # answer seq → events


@dataclass
class Data:
    assignment: Assignment
    questions: list[Question]
    keys: dict[int, AnswerKey]
    students: list[StudentData]


def _load(db: Session, assignment: Assignment, only: Submission | None = None) -> Data:
    questions = questions_of(db, assignment.seq)
    query = select(Submission, Enrollment).join(Enrollment, Submission.enrollment_id == Enrollment.seq).where(
        Submission.assignment_id == assignment.seq
    )
    query = query.where(Submission.seq == only.seq) if only else query.where(Submission.finalized_at.is_not(None))
    students = [StudentData(enrollment=e, sub=s) for s, e in db.execute(query.order_by(Enrollment.student_no))]
    for sd in students:
        sd.answers = {a.question_id: a for a in db.scalars(select(Answer).where(Answer.submission_id == sd.sub.seq))}
        check = db.scalar(select(UnderstandingCheck).where(UnderstandingCheck.submission_id == sd.sub.seq))
        if check:
            rows = db.scalars(select(UnderstandingAnswer).where(UnderstandingAnswer.check_id == check.seq))
            sd.checks = {u.question_id: u for u in rows}
        for a in sd.answers.values():
            sd.concept[a.seq] = list(db.scalars(select(ConceptCheckItem).where(ConceptCheckItem.answer_id == a.seq)))
            sd.pastes[a.seq] = list(db.scalars(select(PasteEvent).where(PasteEvent.answer_id == a.seq)))
    keys = {q.seq: AnswerKey.model_validate(q.answer_key) for q in questions}
    return Data(assignment, questions, keys, students)


# ---------- 이해 확인 (학생) ----------


def _check_items(db: Session, assignment: Assignment) -> list[tuple[Question, Variant]]:
    if not AiPolicy.model_validate(assignment.policy).variant_enabled:
        return []
    out = []
    for q in questions_of(db, assignment.seq):
        v = AnswerKey.model_validate(q.answer_key).variant
        if v is not None:
            out.append((q, v))
    return out


def _explain_target(db: Session, assignment: Assignment, sub: Submission) -> tuple[str, str]:
    """설명할 내 코드: 첫 코드 작성(없으면 간단 제작) 문항에서 낸 답."""
    questions = questions_of(db, assignment.seq)
    for kind in (QuestionType.CODE, QuestionType.PROJECT):
        for i, q in enumerate(questions):
            a = db.scalar(select(Answer).where(Answer.submission_id == sub.seq, Answer.question_id == q.seq))
            if q.type is kind and a is not None and a.content.strip():
                prompt = (f"문항 {i + 1}에서 내가 쓴 코드가 입력을 어떻게 처리해 출력까지 가는지 설명하고, "
                          "요구사항이 조금 바뀌면(예: 입력 범위가 커지면) 어디를 고쳐야 하는지도 적어 주세요.")
                return prompt, a.content
    return "이번 과제에서 가장 어려웠던 문항을 어떻게 풀었는지 설명해 주세요.", ""


def get_check(db: Session, student: User, assignment_id: int) -> UnderstandingCheckOut:
    assignment, sub = _context(db, student, assignment_id)
    db.commit()
    if sub.finalized_at is None:
        raise AppError(ErrorCode.CONFLICT, "최종 제출한 뒤에 이해 확인을 할 수 있어요.")
    prompt, code = _explain_target(db, assignment, sub)
    items = [CheckItem(question_id=q.seq, type=v.type, prompt=v.prompt, code=v.code, choices=v.choices)
             for q, v in _check_items(db, assignment)]  # 정답 · 인정 답안은 보내지 않는다
    done = db.scalar(select(UnderstandingCheck).where(UnderstandingCheck.submission_id == sub.seq)) is not None
    return UnderstandingCheckOut(explain_prompt=prompt, explain_code=code, items=items, submitted=done)


def submit_check(db: Session, student: User, assignment_id: int, body: CheckSubmission) -> CheckReceipt:
    assignment, sub = _context(db, student, assignment_id)
    if sub.finalized_at is None:
        raise AppError(ErrorCode.CONFLICT, "최종 제출한 뒤에 이해 확인을 할 수 있어요.")
    if db.scalar(select(UnderstandingCheck).where(UnderstandingCheck.submission_id == sub.seq)):
        raise AppError(ErrorCode.CONFLICT, "이해 확인은 한 번만 낼 수 있어요.")
    variants = {q.seq: v for q, v in _check_items(db, assignment)}
    seen = [a.question_id for a in body.answers]
    if len(seen) != len(set(seen)) or not set(seen) <= set(variants):
        raise AppError(ErrorCode.VALIDATION_FAILED, "확인 문제 목록에 없는 문항이 있어요.")
    check = UnderstandingCheck(submission_id=sub.seq, explanation=body.explanation, submitted_at=now_kst())
    db.add(check)
    db.flush()
    for a in body.answers:
        correct = variant_correct(variants[a.question_id], a.value)
        db.add(UnderstandingAnswer(check_id=check.seq, question_id=a.question_id, value=a.value,
                                   confidence=a.confidence, is_correct=correct))
    db.commit()
    return CheckReceipt(submitted_at=check.submitted_at)  # 정오는 돌려주지 않는다


# ---------- 문항 하나의 결과 문장 ----------


def _result_text(q: Question, a: Answer | None) -> str:
    if a is None or a.status is not AnswerStatus.SUBMITTED:
        return "미제출"
    if q.type is QuestionType.PROJECT:
        return "채점 대기" if a.score is None else f"{a.score}/{q.points}점"
    if q.type is QuestionType.CODE:
        results = a.test_results or []
        return f"테스트 {sum(r['passed'] for r in results)}/{len(results)} 통과"
    return "정답" if a.is_correct else "오답"


def _variant_text(q: Question, sd: StudentData) -> str:
    u = sd.checks.get(q.seq)
    if u is None:
        return "—"
    return "정답" if u.is_correct else f"오답 ({u.value})"


def _misconception(q: Question, key: AnswerKey, a: Answer | None) -> str | None:
    if a is None or q.type is not QuestionType.MULTIPLE_CHOICE or a.is_correct:
        return None
    return key.misconceptions.get(a.content.strip())


# ---------- 반 리포트 (교수자) ----------


def _mistakes(d: Data, i: int, q: Question) -> QuestionMistakes | None:
    key = d.keys[q.seq]
    answers = [sd.answers[q.seq] for sd in d.students if q.seq in sd.answers
               and sd.answers[q.seq].status is AnswerStatus.SUBMITTED]
    if not answers:
        return None
    n = len(answers)
    if q.type is QuestionType.MULTIPLE_CHOICE:
        picks = Counter(a.content.strip() for a in answers)
        rows = [MistakeRow(label=_choice_label(q, str(c)), rate=_pct(picks[str(c)], n),
                           note=key.misconceptions.get(str(c)), correct=str(c) == key.answer)
                for c in range(len(q.choices))]
        return QuestionMistakes(question_index=i, kind="CHOICE", rows=rows)
    if q.type is QuestionType.SHORT_ANSWER:
        wrong = Counter(_norm(a.content) for a in answers if not a.is_correct)
        rows = [MistakeRow(label=v or "(빈 답)", rate=_pct(c, n), note=None, correct=False)
                for v, c in wrong.most_common(3)]
        return QuestionMistakes(question_index=i, kind="ANSWER", rows=rows) if rows else None
    if q.type is QuestionType.CODE:
        fails: Counter[int] = Counter()
        for a in answers:
            for j, r in enumerate(a.test_results or []):
                if not r["passed"]:
                    fails[j] += 1
        tests = list(q.public_tests) + [t.model_dump() for t in key.hidden_tests]
        rows = []
        for j, c in fails.most_common(3):
            if j < len(tests):
                hidden = " (숨김)" if j >= len(q.public_tests) else ""
                label = f"입력 {tests[j]['input'].strip()[:40] or '(없음)'}{hidden}"
                rows.append(MistakeRow(label=label, rate=_pct(c, n), note=None, correct=False))
        return QuestionMistakes(question_index=i, kind="TEST", rows=rows) if rows else None
    return None


def _supplement(d: Data, mistakes: list[QuestionMistakes]) -> Supplement | None:
    """가장 많이 고른 오개념(또는 가장 많이 틀린 확인 문제)을 보충 대상으로."""
    best: tuple[int, int, str] | None = None  # (rate, question_index, note)
    for m in mistakes:
        for row in m.rows:
            if not row.correct and row.note and (best is None or row.rate > best[0]):
                best = (row.rate, m.question_index, row.note)
    if best is None:
        rates = []
        for i, q in enumerate(d.questions):
            checks = [sd.checks[q.seq] for sd in d.students if q.seq in sd.checks]
            if checks:
                rates.append((_pct(sum(not c.is_correct for c in checks), len(checks)), i))
        if not rates or max(rates)[0] == 0:
            return None
        rate, i = max(rates)
        best = (rate, i, "AI 없이 푼 확인 문제에서 틀린 학생이 많아요")
    rate, i, note = best
    if rate == 0:
        return None
    q = d.questions[i]
    v = d.keys[q.seq].variant
    items = [v.prompt] if v else []
    items.append(f"문항 {i + 1}을 다시 풀고, 힌트 없이 같은 개념을 쓰는 다른 입력으로 확인해 보기")
    return Supplement(question_index=i, rate=rate, summary=f"문항 {i + 1}: {note} ({rate}%).", items=items)


def _cause(q: Question, key: AnswerKey, sd: StudentData) -> str:
    note = _misconception(q, key, sd.answers.get(q.seq))
    if note:
        return note
    u = sd.checks.get(q.seq)
    if u and not u.is_correct and q.type is QuestionType.MULTIPLE_CHOICE:
        return key.misconceptions.get(u.value.strip(), "확인 문제에서 같은 개념을 다시 틀림")
    return "힌트로 원문제를 풀었지만 확인 문제에서 같은 개념을 다시 틀림"


def assignment_report(db: Session, teacher: User, assignment_id: int) -> AssignmentReport:
    assignment = get_owned(db, teacher, assignment_id)
    d = _load(db, assignment)
    graded = [a for sd in d.students for a in sd.answers.values() if a.is_correct is not None]
    checks = [u for sd in d.students for u in sd.checks.values()]
    items = [(sd, i) for sd in d.students for a in sd.answers.values() for i in sd.concept.get(a.seq, [])]
    answered = [(sd, i) for sd, i in items if i.reply is not None]
    pasted_concepts = {a for sd in d.students for a, ev in sd.pastes.items()
                       if any(e.field.value == "CONCEPT_CHECK" for e in ev)}
    ok = [i for sd, i in answered if (i.judgement is ConceptStatus.CONFIRMED if i.judgement else
                                      i.answer_id not in pasted_concepts)]

    stats, mistakes = [], []
    for i, q in enumerate(d.questions):
        qa = [sd.answers[q.seq] for sd in d.students if q.seq in sd.answers]
        auto = [a for a in qa if a.is_correct is not None]
        if q.type is QuestionType.PROJECT:
            scored = [a for a in qa if a.score is not None]
            correct_rate = _pct(sum(a.score >= q.points * 0.6 for a in scored), len(scored))
        else:
            correct_rate = _pct(sum(bool(a.is_correct) for a in auto), len(auto))
        qc = [sd.checks[q.seq] for sd in d.students if q.seq in sd.checks]
        stats.append(QuestionStat(
            question_index=i, type_label=TYPE_LABEL[q.type], correct_rate=correct_rate,
            variant_rate=_pct(sum(c.is_correct for c in qc), len(qc)) if d.keys[q.seq].variant else None,
            avg_hint_steps=round(sum(a.hint_step for a in qa) / len(qa), 1) if qa else 0.0,
        ))
        m = _mistakes(d, i, q)
        if m:
            mistakes.append(m)

    dependency, signal_rows = [], []
    for sd in d.students:
        name = sd.enrollment.student_no
        for i, q in enumerate(d.questions):
            a = sd.answers.get(q.seq)
            if a is None:
                continue
            u = sd.checks.get(q.seq)
            if a.hint_step >= 2 and u is not None and not u.is_correct:
                dependency.append(DependencyRow(
                    student_id=sd.enrollment.student_id, student_name=name, question_index=i,
                    hint_steps=a.hint_step, variant_answer=u.value,
                    cause=_cause(q, d.keys[q.seq], sd),
                ))
            sig = paste_signals(db, a)
            if sig:
                signal_rows.append(SignalRow(student_id=sd.enrollment.student_id, student_name=name,
                                             question_index=i, signals=sig))

    return AssignmentReport(
        assignment_id=assignment.seq, title=assignment.title, submitted_count=len(d.students),
        student_count=approved_count(db, assignment.class_id),
        assisted_correct_rate=_pct(sum(bool(a.is_correct) for a in graded), len(graded)),
        alone_variant_rate=(_pct(sum(u.is_correct for u in checks), len(checks))
                            if any(k.variant for k in d.keys.values()) else None),
        concept_check_ok_rate=_pct(len(ok), len(answered)),
        question_stats=stats, mistakes=mistakes, supplement=_supplement(d, mistakes),
        dependency=dependency, signals=signal_rows,
    )


# ---------- 점수 합계 ----------


def _totals(d: Data, sd: StudentData) -> tuple[int, int, int, int]:
    """(점수, 만점, 채점 대기 배점, 힌트 단계 합)."""
    score = max_score = pending = hints = 0
    for q in d.questions:
        max_score += q.points
        a = sd.answers.get(q.seq)
        if a is None:
            continue
        hints += a.hint_step
        if a.score is None:
            if q.type is QuestionType.PROJECT and a.status is AnswerStatus.SUBMITTED:
                pending += q.points
        else:
            score += a.score
    return score, max_score, pending, hints


# ---------- 학생별 기록 (교수자) ----------


def _classification(m: ChatMessage) -> str:
    if m.uncertain:
        return "모호함"
    if m.is_learning_context is False:
        return "과제와 무관"
    if m.requests_complete_answer:
        return "완성 답안 요청"
    if m.has_self_attempt_evidence:
        return "풀이 공유"
    return "학습 질문"


def student_record(db: Session, teacher: User, assignment_id: int, student_id: int) -> StudentRecord:
    assignment = get_owned(db, teacher, assignment_id)
    enrollment = db.scalar(select(Enrollment).where(Enrollment.class_id == assignment.class_id,
                                                    Enrollment.student_id == student_id))
    if enrollment is None:
        raise AppError(ErrorCode.NOT_FOUND)
    sub = db.scalar(select(Submission).where(Submission.assignment_id == assignment.seq,
                                             Submission.enrollment_id == enrollment.seq))
    if sub is None:
        raise AppError(ErrorCode.NOT_FOUND, "이 학생은 아직 이 과제를 시작하지 않았어요.")
    d = _load(db, assignment, only=sub)
    sd = d.students[0]
    score, max_score, pending, hints = _totals(d, sd)

    rows = []
    for i, q in enumerate(d.questions):
        a = sd.answers.get(q.seq)
        items = sd.concept.get(a.seq, []) if a else []
        concept = "—" if not items else ("설명 확인" if all(x.reply for x in items) else "답변 대기")
        sig = paste_signals(db, a) if a else []
        rows.append(RecordRow(question_index=i, hint_steps=a.hint_step if a else 0, result=_result_text(q, a),
                              variant=_variant_text(q, sd), concept_check=concept, signal=", ".join(sig) or None))

    variant_total = len(sd.checks)
    variant_passed = sum(u.is_correct for u in sd.checks.values())
    hint_only = [str(i + 1) for i, q in enumerate(d.questions)
                 if (u := sd.checks.get(q.seq)) and not u.is_correct and (a := sd.answers.get(q.seq)) and a.is_correct]
    variant_note = f"문항 {'·'.join(hint_only)}은 원문제만 맞힘" if hint_only else ""

    others = _load(db, assignment).students
    class_hints = [sum(a.hint_step for a in o.answers.values()) for o in others]
    conversation = None
    if sd.answers:
        top = max(sd.answers.values(), key=lambda a: (a.hint_step, -a.seq))
        msgs = list(db.scalars(select(ChatMessage).where(ChatMessage.answer_id == top.seq)
                               .order_by(ChatMessage.created_at, ChatMessage.seq)))
        turns = []
        for j, m in enumerate(msgs):
            if m.role is not ChatRole.STUDENT or m.help_choice is not None:
                continue
            reply = next((x for x in msgs[j + 1:] if x.role is ChatRole.ASSISTANT), None)
            turns.append(RecordTurn(message=m.content, classification=_classification(m),
                                    attempt=bool(m.has_self_attempt_evidence),
                                    leak_blocked=bool(reply and reply.leak_blocked)))
        if turns:
            qi = next(i for i, q in enumerate(d.questions) if q.seq == top.question_id)
            q = d.questions[qi]
            u = sd.checks.get(q.seq)
            parts = [f"힌트 {top.hint_step}단계를 받았어요."]
            if any(t.leak_blocked for t in turns):
                parts.append("AI 답변 중 정답 · 완성 코드가 들어간 답이 막힌 적이 있어요.")
            if u is not None:
                parts.append("확인 문제는 맞혔어요." if u.is_correct else
                             f"확인 문제에서 다시 틀렸어요({_cause(q, d.keys[q.seq], sd)}).")
            parts.append("확정 판정이 아니라 교수자가 확인할 근거예요.")
            conversation = RecordConversation(question_index=qi, turns=turns, note=" ".join(parts))

    return StudentRecord(
        student_id=student_id, student_name=enrollment.student_no, assignment_title=assignment.title,
        score=score, max_score=max_score, pending_points=pending, variant_passed=variant_passed,
        variant_total=variant_total, variant_note=variant_note, hint_steps=hints,
        class_avg_hint_steps=round(sum(class_hints) / len(class_hints), 1) if class_hints else 0.0,
        rows=rows, conversation=conversation,
    )


# ---------- 내 리포트 (학생) ----------


def _correct_answer(q: Question, key: AnswerKey) -> str:
    if q.type is QuestionType.MULTIPLE_CHOICE and key.answer:
        return _choice_label(q, key.answer)
    if q.type is QuestionType.SHORT_ANSWER:
        return key.answer or ""
    if q.type is QuestionType.CODE:
        return key.model_answer or "공개 · 숨김 테스트를 모두 통과하는 코드"
    return "교수자 채점 후 피드백이 표시돼요"


def my_report(db: Session, student: User, assignment_id: int) -> MyReport | MyReportPending:
    assignment, sub = _context(db, student, assignment_id)
    db.commit()
    if assignment.results_released_at is None:
        return MyReportPending(assignment_title=assignment.title)  # 공개 전: 정오 · 점수 없음
    d = _load(db, assignment, only=sub)
    sd = d.students[0]
    score, max_score, pending, hints = _totals(d, sd)

    concepts, misconceptions, overconfident, next_steps, questions = [], [], [], [], []
    for i, q in enumerate(d.questions):
        key, a, u = d.keys[q.seq], sd.answers.get(q.seq), sd.checks.get(q.seq)
        label = f"문항 {i + 1} ({TYPE_LABEL[q.type]})"
        result = _result_text(q, a)
        if a and a.hint_step:
            result += f" (힌트 {a.hint_step}단계)"
        if a and a.feedback:
            result += f" — {a.feedback}"
        questions.append(MyQuestionResult(question_index=i, type_label=TYPE_LABEL[q.type], result=result,
                                          correct_answer=_correct_answer(q, key)))
        note = _misconception(q, key, a)
        if note:
            misconceptions.append(f"문항 {i + 1}: {note}")
        if u and not u.is_correct and u.confidence is Confidence.SURE:
            overconfident.append(f"문항 {i + 1} 확인 문제")
        if q.type is QuestionType.PROJECT or a is None:
            continue
        hint = a.hint_step
        if a.is_correct and (u is None or u.is_correct) and hint <= 1:
            status, reason = ConceptStatus.CONFIRMED, (
                "원문제를 " + ("힌트 없이" if hint == 0 else "힌트 1단계로") + " 맞혔고"
                + (", AI 없는 확인 문제도 맞혔어요." if u else " 확인 문제는 없었어요."))
        elif u is not None and not u.is_correct:
            status = ConceptStatus.NEEDS_WORK
            lead = "원문제는 맞혔지만" if a.is_correct else "원문제와"
            reason = f"{lead} AI 없는 확인 문제에서 {u.value}로 답했어요."
            next_steps.append(f"문항 {i + 1} 다시 보기: " + (key.variant.prompt if key.variant else q.prompt[:60]))
        elif not a.is_correct:
            status, reason = ConceptStatus.NEEDS_WORK, "원문제 결과가 기대와 달랐어요."
            next_steps.append(f"문항 {i + 1}의 정답 · 풀이를 확인하고 다시 풀어 보기")
        else:
            status = ConceptStatus.UNCLEAR
            reason = f"맞혔지만 힌트 {hint}단계를 받아서 혼자 할 수 있는지 판단 근거가 부족해요."
        concepts.append(ConceptRow(name=label, status=status, reason=reason))

    return MyReport(
        assignment_title=assignment.title, score=score, max_score=max_score, pending_points=pending,
        hint_steps=hints, concepts=concepts, misconceptions=misconceptions, overconfident=overconfident,
        next_steps=next_steps or ["모든 문항을 확인했어요. 다음 과제에서는 힌트 단계를 줄여 보세요."],
        questions=questions,
    )
