"""교수자 문항(QuestionData) ↔ 테이블 값 변환. 공개·숨김 테스트를 나누고 합친다(④ 설계 A1)."""

from typing import Any

from app.models import Question
from app.schemas.assignments import AnswerKey, IOTest, QuestionData, TestCase


def _io(test: TestCase) -> dict[str, str]:
    return IOTest(input=test.input, expected_output=test.expected_output).model_dump()


def to_columns(question: QuestionData, position: int) -> dict[str, Any]:
    key = AnswerKey(
        answer=question.answer or None,
        accepted_answers=question.accepted_answers,
        misconceptions=question.misconceptions,
        hidden_tests=[IOTest.model_validate(_io(t)) for t in question.tests if t.hidden],
        rubric=question.rubric,
        model_answer=question.model_answer or None,
        variant=question.variant,
    )
    return {
        "position": position,
        "type": question.type,
        "points": question.points,
        "prompt": question.prompt,
        "code": question.code,
        "choices": list(question.choices),
        "starter_code": question.starter_code,
        "public_tests": [_io(t) for t in question.tests if not t.hidden],
        "ai_help": question.ai_help,
        "answer_key": key.model_dump(mode="json"),
    }


def to_data(question: Question) -> QuestionData:
    key = AnswerKey.model_validate(question.answer_key)
    tests = [TestCase(**t) for t in question.public_tests]
    tests += [TestCase(**t.model_dump(), hidden=True) for t in key.hidden_tests]
    return QuestionData(
        seq=question.seq, type=question.type, points=question.points, prompt=question.prompt, code=question.code,
        choices=list(question.choices), answer=key.answer or "", accepted_answers=key.accepted_answers,
        misconceptions=key.misconceptions, starter_code=question.starter_code, tests=tests, rubric=key.rubric,
        model_answer=key.model_answer or "", ai_help=question.ai_help, variant=key.variant,
    )


COLUMNS = ("position", "type", "points", "prompt", "code", "choices", "starter_code", "public_tests", "ai_help",
           "answer_key")


def _stored(question: Question) -> dict[str, Any]:
    return {name: getattr(question, name) for name in COLUMNS}


def same_questions(current: list[Question], incoming: list[QuestionData]) -> bool:
    """배포 후 잠금(A3 · A4): 개수 · 순서 · 내용 · 공개/숨김까지 같아야 같은 문항."""
    if len(current) != len(incoming):
        return False
    ordered = sorted(current, key=lambda q: q.position)
    return all(_stored(q) == to_columns(data, i) for i, (q, data) in enumerate(zip(ordered, incoming, strict=True)))
