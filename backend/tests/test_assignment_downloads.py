"""새 과제 화면에서 내려받는 양식 · 예시 파일이 실제로 읽히는지 (frontend/public)."""

from pathlib import Path

from app.services import assignment_md as md

PUBLIC = Path(__file__).resolve().parents[2] / "frontend" / "public"
TEMPLATE = PUBLIC / "thinkguard-assignment-template.md"
EXAMPLE = PUBLIC / "thinkguard-assignment-example.md"


def _body(text: str) -> str:
    """'## 과제 정보'부터 끝까지 (맨 위 안내 문구는 빼고 비교)"""
    return text[text.index("## 과제 정보"):]


def test_template_parses_with_one_question_per_type():
    data = md.parse(TEMPLATE.read_text(encoding="utf-8"))
    assert [q.type.value for q in data.questions] == ["MULTIPLE_CHOICE", "SHORT_ANSWER", "CODE", "PROJECT"]
    assert sum(q.points for q in data.questions) == 100


def test_example_parses_into_sample_questions():
    data = md.parse(EXAMPLE.read_text(encoding="utf-8"))
    assert len(data.questions) == 5


def test_example_matches_seed_sample():
    # 예시 파일은 시드 샘플과 내용이 같아야 한다(안내 문구만 다름)
    assert _body(EXAMPLE.read_text(encoding="utf-8")) == _body(md.sample_text())
