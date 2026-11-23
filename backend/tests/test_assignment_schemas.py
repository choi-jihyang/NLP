from datetime import datetime

import pytest
from pydantic import ValidationError

from app.core.enums import Language, QuestionType
from app.models import Question
from app.schemas.assignments import AssignmentData, QuestionData
from app.services.question_codec import same_questions, to_columns, to_data

MC = {"type": "MULTIPLE_CHOICE", "points": 10, "prompt": "1011은?", "choices": ["11", "13"], "answer": "0"}
SA = {"type": "SHORT_ANSWER", "points": 10, "prompt": "출력은?", "code": "printf(\"1101\");", "answer": "1101"}
CODE = {
    "type": "CODE", "points": 20, "prompt": "변환기", "starter_code": "int main(void) {}",
    "tests": [
        {"input": "5", "expected_output": "101"},
        {"input": "255", "expected_output": "11111111", "hidden": True},
    ],
    "model_answer": "int main(void) { return 0; }",
}
PROJECT = {"type": "PROJECT", "points": 35, "prompt": "뺄셈기", "rubric": ["음수 처리"], "ai_help": False}


def _q(base: dict, **changes: object) -> QuestionData:
    return QuestionData.model_validate({**base, **changes})


def test_valid_questions_of_each_type():
    for base in (MC, SA, CODE, PROJECT):
        assert _q(base).type == base["type"]


@pytest.mark.parametrize("answer", ["5", "-1", "a", "", "2"])
def test_multiple_choice_answer_must_be_a_choice_index(answer: str):
    with pytest.raises(ValidationError):
        _q(MC, answer=answer)


def test_multiple_choice_needs_two_choices():
    with pytest.raises(ValidationError):
        _q(MC, choices=["11"])


def test_short_answer_needs_answer():
    with pytest.raises(ValidationError):
        _q(SA, answer="   ")


@pytest.mark.parametrize(
    "tests",
    [[], [{"input": "1", "expected_output": ""}], [{"input": "x" * 10_001, "expected_output": "1"}]],
)
def test_code_question_tests_rules(tests: list):
    with pytest.raises(ValidationError):
        _q(CODE, tests=tests)


def test_project_needs_non_blank_rubric():
    with pytest.raises(ValidationError):
        _q(PROJECT, rubric=["  "])


def test_assignment_limits():
    base = {"title": "2진수 과제", "language": "C"}
    assert AssignmentData.model_validate(base).title == "2진수 과제"
    with pytest.raises(ValidationError):
        AssignmentData.model_validate({**base, "title": "   "})
    with pytest.raises(ValidationError):
        AssignmentData.model_validate({**base, "questions": [MC] * 51})
    with pytest.raises(ValidationError):
        AssignmentData.model_validate({**base, "due_at": datetime(2026, 12, 5, 23, 59).isoformat()})  # 시간대 없음
    with pytest.raises(ValidationError):
        AssignmentData.model_validate({**base, "language": "Python"})  # 대문자 Enum만


def test_to_columns_splits_tests_and_hides_key():
    cols = to_columns(_q(CODE), position=2)
    assert cols["position"] == 2 and cols["type"] == QuestionType.CODE
    assert cols["public_tests"] == [{"input": "5", "expected_output": "101"}]
    assert cols["answer_key"]["hidden_tests"] == [{"input": "255", "expected_output": "11111111"}]
    assert cols["answer_key"]["model_answer"] == "int main(void) { return 0; }"
    assert cols["answer_key"]["answer"] is None  # 빈 정답은 null로 저장


def test_to_data_round_trip():
    for base in (MC, SA, CODE, PROJECT):
        question = Question(seq=7, assignment_id=1, **to_columns(_q(base), position=0))
        data = to_data(question)
        assert data.seq == 7
        assert data.model_dump(exclude={"seq"}) == _q(base).model_dump(exclude={"seq"})


def _stored(items: list[dict]) -> list[Question]:
    return [Question(seq=i + 1, assignment_id=1, **to_columns(_q(b), position=i)) for i, b in enumerate(items)]


def test_same_questions_detects_changes():
    stored = _stored([MC, CODE])
    assert same_questions(stored, [_q(MC), _q(CODE)])
    assert not same_questions(stored, [_q(CODE), _q(MC)])  # 순서
    assert not same_questions(stored, [_q(MC)])  # 개수
    flipped = {**CODE, "tests": [{**t, "hidden": not t.get("hidden", False)} for t in CODE["tests"]]}
    assert not same_questions(stored, [_q(MC), _q(flipped)])  # 숨김 표시
    assert not same_questions(stored, [_q(MC, prompt="바뀐 문제"), _q(CODE)])  # 내용


def test_language_values():
    assert {lang.value for lang in Language} == {"PYTHON", "JAVA", "C", "JAVASCRIPT"}
