"""학생용 과제 응답. 🔒 값(정답 · 인정 답안 · 오개념 · 숨김 테스트 · 채점 기준 · 모범 답안 · 확인 문제)을
담을 필드가 아예 없다 — 직렬화 실수로 새지 않게 구조로 막는다(불변식 I8)."""

from datetime import datetime

from pydantic import BaseModel

from app.core.enums import HintMode, Language, QuestionType

HINT_MODE_LABEL: dict[HintMode, str] = {
    HintMode.NONE: "힌트 없음",
    HintMode.CONCEPT: "개념만",
    HintMode.STEP: "한 단계씩",
    HintMode.EARNED: "시도한 만큼 열기",
}
MAX_HINT_STEPS: dict[HintMode, int] = {HintMode.NONE: 0, HintMode.CONCEPT: 1, HintMode.STEP: 3, HintMode.EARNED: 3}


class StudentTest(BaseModel):
    input: str
    expected_output: str


class StudentQuestion(BaseModel):
    seq: int
    type: QuestionType
    points: int
    prompt: str
    code: str
    choices: list[str]
    starter_code: str
    ai_help: bool
    ai_enabled: bool  # 간단 제작은 ai_help, 그 외는 항상 True
    public_tests: list[StudentTest]
    hidden_test_count: int


class StudentAssignment(BaseModel):
    seq: int
    title: str
    course: str
    language: Language
    due_at: datetime | None
    hint_mode: HintMode
    hint_mode_label: str
    max_hint_steps: int
    external_signal_enabled: bool
    questions: list[StudentQuestion]
