"""md 과제 파일 → AssignmentData 초안 (scope ③, 샘플 docs/spec/samples/c-binary-assignment.md).

규칙(정규식)으로만 읽는다. 양식이 다르면 어디가 틀렸는지 모아서 한 번에 알려 준다(MdFormatError).
양식 문서: docs/spec/assignment-md-format.md

- 선택지 번호 · 객관식 정답 · 오개념 번호는 파일에서 1부터 쓰고, 저장 모양은 0부터(schema AnswerKey).
- `[교수자 전용]` 표시는 읽을 때 지운다. 어느 칸이 학생에게 보이는지는 칸 이름이 정한다(학생 스키마 I8).
"""

import re
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from app.core.clock import KST
from app.core.enums import Language, QuestionType
from app.schemas.ai_policy import AiPolicy
from app.schemas.assignments import AssignmentData, QuestionData, TestCase, Variant

SAMPLE_PATH = Path(__file__).resolve().parents[3] / "docs" / "spec" / "samples" / "c-binary-assignment.md"
MAX_BYTES = 200_000

TYPE_NAMES = {
    "객관식": QuestionType.MULTIPLE_CHOICE,
    "출력 예측": QuestionType.SHORT_ANSWER,
    "코드 작성": QuestionType.CODE,
    "간단 제작": QuestionType.PROJECT,
}
LANGUAGE_NAMES = {"c": Language.C, "python": Language.PYTHON, "java": Language.JAVA, "javascript": Language.JAVASCRIPT}
AI_HELP_NAMES = {"사용": True, "사용 안 함": False, "사용안함": False, "끔": False}

_TEACHER_ONLY = re.compile(r"\s*\[교수자 전용\]\s*$")
_QUESTION_HEAD = re.compile(r"^##\s+문항\s*(\d+)\s*$", re.M)
_H2 = re.compile(r"^##\s+(.+?)\s*$", re.M)
_H3 = re.compile(r"^###\s+(.+?)\s*$", re.M)
_BULLET = re.compile(r"^\s*-\s*([^:：]+?)\s*[:：]\s*(.*?)\s*$")
_NUMBERED = re.compile(r"^\s*(\d+)[.)]\s+(.*?)\s*$")
_FENCE = re.compile(r"```[^\n]*\n(.*?)\n?```", re.S)
_RULE = re.compile(r"^\s*-{3,}\s*$", re.M)
_TRAILING_RULE = re.compile(r"\n\s*-{3,}\s*$")


class MdFormatError(ValueError):
    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


# ---------- 작은 도우미 ----------


def _sections(text: str, heading: re.Pattern[str]) -> list[tuple[str, str]]:
    """제목 패턴으로 나눈 (제목, 본문) 목록."""
    marks = list(heading.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = _TRAILING_RULE.sub("", text[m.end():end])  # 문항 사이 구분선(---)은 본문이 아니다
        out.append((_TEACHER_ONLY.sub("", m.group(1)).strip(), body.strip("\n")))
    return out


def _bullets(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = _BULLET.match(line)
        if m:
            out.setdefault(m.group(1).strip(), m.group(2).strip())
    return out


def _list_items(text: str) -> list[str]:
    return [m.group(1).strip() for line in text.splitlines() if (m := re.match(r"^\s*-\s+(.*\S)\s*$", line))]


def _code(text: str) -> str:
    m = _FENCE.search(text)
    return (m.group(1) if m else text).strip("\n")


def _one_based(value: str, count: int, where: str, problems: list[str]) -> str:
    """파일의 1부터 번호 → 저장용 0부터 번호 문자열."""
    if not re.fullmatch(r"[1-9][0-9]*", value.strip()) or int(value) > count:
        problems.append(f"{where}: 1부터 {count} 사이의 선택지 번호여야 해요 (지금: {value!r})")
        return "0"
    return str(int(value) - 1)


def parse_tests(text: str, where: str, problems: list[str], hidden: bool = False) -> list[TestCase]:
    """```text 블록 안: '입력: …' / '출력: …' 묶음을 '---'로 나눈다. 값은 여러 줄이어도 된다."""
    tests = []
    for i, chunk in enumerate(_RULE.split(_code(text)), start=1):
        if not chunk.strip():
            continue
        m = re.match(r"\s*입력\s*[:：][ \t]?(.*?)\n\s*출력\s*[:：][ \t]?(.*)$", chunk, re.S)
        if not m:
            problems.append(f"{where} {i}번째: '입력:' 다음 줄에 '출력:'이 있어야 해요")
            continue
        inp, out = m.group(1).rstrip("\n"), m.group(2).strip("\n")
        if not out.strip():
            problems.append(f"{where} {i}번째: 출력이 비어 있어요")
            continue
        tests.append(TestCase(input=inp + "\n" if inp else "", expected_output=out, hidden=hidden))
    if not tests:
        problems.append(f"{where}: 테스트를 하나도 읽지 못했어요")
    return tests


def _variant(text: str, where: str, problems: list[str]) -> Variant | None:
    info = _bullets(text)
    kind = TYPE_NAMES.get(info.get("유형", ""))
    if kind not in (QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER):
        problems.append(f"{where}: 유형은 '객관식' 또는 '출력 예측'이어야 해요")
        return None
    choices: list[str] = []
    answer = info.get("정답", "")
    if kind is QuestionType.MULTIPLE_CHOICE:
        choices = [re.sub(r"^\s*\d+[.)]\s*", "", c).strip() for c in info.get("선택지", "").split("/") if c.strip()]
        answer = _one_based(answer, len(choices), f"{where} 정답", problems)
    try:
        return Variant(type=kind, prompt=info.get("문제", ""), code=_code(text) if "```" in text else "",
                       choices=choices, answer=answer, accepted_answers=_list_items(info.get("인정 답안", "")))
    except ValidationError as exc:
        problems.append(f"{where}: {_first_error(exc)}")
        return None


def _first_error(exc: ValidationError) -> str:
    err = exc.errors()[0]
    return str(err.get("msg", "형식 오류")).removeprefix("Value error, ")


# ---------- 문항 ----------


def _question(number: str, body: str, problems: list[str]) -> QuestionData | None:
    where = f"문항 {number}"
    head = body.split("\n###", 1)[0]
    info = _bullets(head)
    subs = dict(_sections(body, _H3))

    kind = TYPE_NAMES.get(info.get("유형", ""))
    if kind is None:
        problems.append(f"{where}: '- 유형:'은 {', '.join(TYPE_NAMES)} 중 하나여야 해요")
        return None
    points_text = info.get("배점", "")
    if not points_text.isdigit():
        problems.append(f"{where}: '- 배점:'은 0 이상의 정수여야 해요")
        points_text = "0"
    ai_help_text = info.get("AI 도움", "사용")
    if ai_help_text not in AI_HELP_NAMES:
        problems.append(f"{where}: '- AI 도움:'은 '사용' 또는 '사용 안 함'이어야 해요")
    prompt = subs.get("문제", "").strip()
    if not prompt:
        problems.append(f"{where}: '### 문제'가 없거나 비어 있어요")
        prompt = "-"

    fields: dict[str, object] = {
        "type": kind, "points": int(points_text), "prompt": prompt,
        "ai_help": AI_HELP_NAMES.get(ai_help_text, True),
        "code": _code(subs["코드"]) if "코드" in subs else "",
        "model_answer": _code(subs["모범 답안"]) if "모범 답안" in subs else "",
        "accepted_answers": _list_items(subs.get("인정 답안", "")),
    }
    if kind is QuestionType.MULTIPLE_CHOICE:
        choices = [m.group(2) for line in subs.get("선택지", "").splitlines() if (m := _NUMBERED.match(line))]
        fields["choices"] = choices
        fields["answer"] = _one_based(subs.get("정답", "").strip(), len(choices), f"{where} 정답", problems)
        miscon = {}
        for key, val in _bullets(subs.get("오개념", "")).items():
            miscon[_one_based(key, len(choices), f"{where} 오개념 번호", problems)] = val
        fields["misconceptions"] = miscon
    elif kind is QuestionType.SHORT_ANSWER:
        fields["answer"] = subs.get("정답", "").strip()
    elif kind is QuestionType.CODE:
        fields["starter_code"] = _code(subs["시작 코드"]) if "시작 코드" in subs else ""
        tests = parse_tests(subs["공개 테스트"], f"{where} 공개 테스트", problems) if "공개 테스트" in subs else []
        if "숨김 테스트" in subs:
            tests += parse_tests(subs["숨김 테스트"], f"{where} 숨김 테스트", problems, hidden=True)
        if not tests:
            problems.append(f"{where}: 코드 작성 문항은 '### 공개 테스트' 또는 '### 숨김 테스트'가 있어야 해요")
        fields["tests"] = tests
    elif kind is QuestionType.PROJECT:
        fields["rubric"] = _list_items(subs.get("채점 기준", ""))
        if "참고 입출력" in subs:  # 저장 칸이 따로 없어서 채점 기준 뒤에 교수자 참고로 붙인다
            fields["rubric"] = [*fields["rubric"], "참고 입출력:\n" + _code(subs["참고 입출력"])]
    if "확인 문제" in subs:
        fields["variant"] = _variant(subs["확인 문제"], f"{where} 확인 문제", problems)

    try:
        return QuestionData.model_validate(fields)
    except ValidationError as exc:
        problems.append(f"{where}: {_first_error(exc)}")
        return None


# ---------- 전체 ----------


def _due(text: str, problems: list[str]) -> datetime | None:
    if not text:
        return None
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d %H:%M").replace(tzinfo=KST)
    except ValueError:
        problems.append(f"과제 정보: 마감은 'YYYY-MM-DD HH:MM'(한국 시간)이어야 해요 (지금: {text!r})")
        return None


def parse(text: str, policy: AiPolicy | None = None, class_id: int | None = None) -> AssignmentData:
    """md 본문 → 저장 전 초안. 양식 오류는 모두 모아 MdFormatError."""
    problems: list[str] = []
    text = text.replace("\r\n", "\n").lstrip("﻿")
    h2 = dict(_sections(text, _H2))
    info = _bullets(h2.get("과제 정보", ""))
    if "과제 정보" not in h2:
        problems.append("'## 과제 정보' 칸이 없어요")

    h1 = re.search(r"^#\s+(?:과제\s*[:：]\s*)?(.+)$", text, re.M)
    title = info.get("제목") or (h1.group(1).strip() if h1 else "")
    if not title:
        problems.append("과제 정보: '- 제목:'이 없어요")
    lang_text = info.get("언어", "")
    language = LANGUAGE_NAMES.get(lang_text.strip().lower())
    if language is None:
        problems.append(f"과제 정보: '- 언어:'는 C · Python · Java · JavaScript 중 하나여야 해요 (지금: {lang_text!r})")

    numbers = _QUESTION_HEAD.findall(text)
    if not numbers:
        problems.append("'## 문항 1'처럼 시작하는 문항이 하나도 없어요")
    questions = []
    for number, body in zip(numbers, [b for t, b in _sections(text, _H2) if re.fullmatch(r"문항\s*\d+", t)],
                            strict=True):
        q = _question(number, body, problems)
        if q is not None:
            questions.append(q)

    due_at = _due(info.get("마감", ""), problems)
    if problems:
        raise MdFormatError(problems)
    try:
        return AssignmentData(
            class_id=class_id, title=title[:100], course=info.get("과목", "")[:100],
            audience=info.get("대상", "")[:100], language=language, description=info.get("설명", ""),
            due_at=due_at, policy=policy or AiPolicy(), questions=questions,
        )
    except ValidationError as exc:
        raise MdFormatError([f"과제 정보: {_first_error(exc)}"]) from exc


def decode(raw: bytes) -> str:
    if len(raw) > MAX_BYTES:
        raise MdFormatError([f"파일이 너무 커요 ({MAX_BYTES // 1000}KB 이하만 받아요)"])
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MdFormatError(["UTF-8 텍스트(.md) 파일만 읽을 수 있어요"]) from exc


def sample_text() -> str:
    return SAMPLE_PATH.read_text(encoding="utf-8")
