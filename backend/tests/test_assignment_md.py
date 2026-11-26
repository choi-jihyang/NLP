"""md 과제 파일 파서 (assignment_md) · /extract · SAMPLE 초안 · 미리보기 · 지시문 초안."""

import pytest
from fastapi.testclient import TestClient

from app.core.enums import Language, QuestionType
from app.services import assignment_md as md
from tests.factories import api_class, api_teacher, bearer

SAMPLE = md.sample_text()


def test_sample_parses_into_five_questions():
    d = md.parse(SAMPLE)
    assert d.title == "2진수 변환기 · 덧셈기 · 뺄셈기"
    assert (d.course, d.audience, d.language) == ("프로그래밍 기초", "컴퓨터공학과 1학년", Language.C)
    assert d.due_at is not None and d.due_at.isoformat() == "2026-12-05T23:59:00+09:00"
    assert [q.type for q in d.questions] == [QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER,
                                            QuestionType.CODE, QuestionType.CODE, QuestionType.PROJECT]
    assert [q.points for q in d.questions] == [10, 10, 20, 25, 35]


def test_multiple_choice_numbers_become_zero_based():
    q = md.parse(SAMPLE).questions[0]
    assert q.choices == ["11", "13", "1011", "3"]
    assert q.answer == "0"  # 파일의 "1"
    assert set(q.misconceptions) == {"1", "2", "3"}  # 파일의 2 · 3 · 4
    assert q.variant is not None and q.variant.answer == "0" and q.variant.choices[0] == "13"


def test_short_answer_code_and_accepted_answers():
    q = md.parse(SAMPLE).questions[1]
    assert q.answer == "1101" and q.accepted_answers == ["1101", "1 1 0 1"]
    assert q.code.startswith("#include <stdio.h>") and "```" not in q.code
    assert q.variant is not None and q.variant.answer == "0110"


def test_code_question_tests_split_public_and_hidden():
    q = md.parse(SAMPLE).questions[2]
    public = [(t.input, t.expected_output) for t in q.tests if not t.hidden]
    hidden = [(t.input, t.expected_output) for t in q.tests if t.hidden]
    assert public == [("5\n", "101"), ("0\n", "0"), ("8\n", "1000")]
    assert hidden[-1] == ("1000000\n", "11110100001001000000")
    assert "print_binary" in q.starter_code and "bits[33]" in q.model_answer


def test_project_rubric_and_reference_io():
    q = md.parse(SAMPLE).questions[4]
    assert q.ai_help is True and len(q.rubric) == 6
    assert q.rubric[-1].startswith("참고 입출력:")


def test_teacher_only_marks_and_separators_do_not_leak_into_fields():
    d = md.parse(SAMPLE)
    for q in d.questions:
        for text in (q.prompt, q.code, q.starter_code, q.model_answer, *q.rubric):
            assert "[교수자 전용]" not in text
        assert not q.prompt.rstrip().endswith("---")


BROKEN = """# 과제: 깨진 과제

## 과제 정보
- 제목: 깨진 과제
- 언어: 코볼
- 마감: 12월 5일

## 문항 1
- 유형: 서술형
- 배점: 10

## 문항 2
- 유형: 객관식
- 배점: 열

### 문제
고르시오

### 선택지
1. 가
2. 나

### 정답 [교수자 전용]
5

## 문항 3
- 유형: 코드 작성
- 배점: 5

### 문제
짜시오

### 공개 테스트
```text
출력만 있음
```
"""


def test_format_errors_are_collected_with_locations():
    with pytest.raises(md.MdFormatError) as exc:
        md.parse(BROKEN)
    problems = "\n".join(exc.value.problems)
    for expected in ["언어", "마감", "문항 1", "문항 2: '- 배점:'", "문항 2 정답", "문항 3 공개 테스트"]:
        assert expected in problems, problems


def test_missing_questions_is_an_error():
    with pytest.raises(md.MdFormatError, match="문항"):
        md.parse("## 과제 정보\n- 제목: x\n- 언어: C\n")


def test_multiline_test_values():
    text = SAMPLE.replace("입력: 5\n출력: 101", "입력: 5\n7\n출력: 101\n111")
    q = md.parse(text).questions[2]
    assert (q.tests[0].input, q.tests[0].expected_output) == ("5\n7\n", "101\n111")


def test_decode_rejects_non_utf8_and_huge_files():
    with pytest.raises(md.MdFormatError):
        md.decode("한글".encode("cp949"))
    with pytest.raises(md.MdFormatError):
        md.decode(b"x" * (md.MAX_BYTES + 1))


# ---- API ---------------------------------------------------------------------


def test_extract_endpoint_returns_unsaved_draft_with_class_policy(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    client.put(f"/api/classes/{klass['seq']}/ai-defaults", json={"hint_mode": "STEP", "code_line_limit": 2},
               headers=teacher)
    res = client.post(f"/api/classes/{klass['seq']}/assignments/extract", headers=teacher,
                      files={"file": ("c-binary.md", SAMPLE.encode(), "text/markdown")})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["seq"] is None and body["class_id"] == klass["seq"]
    assert len(body["questions"]) == 5 and body["policy"]["hint_mode"] == "STEP"
    # 저장되지 않았다
    assert client.get(f"/api/classes/{klass['seq']}/assignments", headers=teacher).json() == []
    # 그대로 저장할 수 있다
    saved = client.post(f"/api/classes/{klass['seq']}/assignments", json=body, headers=teacher)
    assert saved.status_code == 201, saved.text


def test_extract_format_error_is_validation_failed_with_details(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    res = client.post(f"/api/classes/{klass['seq']}/assignments/extract", headers=teacher,
                      files={"file": ("broken.md", BROKEN.encode(), "text/markdown")})
    assert res.status_code == 400
    assert res.json()["code"] == "VALIDATION_FAILED" and "문항 3 공개 테스트" in res.json()["message"]


def test_extract_rejects_pdf_and_other_class(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    pdf = client.post(f"/api/classes/{klass['seq']}/assignments/extract", headers=teacher,
                      files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")})
    assert pdf.status_code == 400 and ".md" in pdf.json()["message"]
    other = api_teacher(client, email="other@example.test")
    res = client.post(f"/api/classes/{klass['seq']}/assignments/extract", headers=other,
                      files={"file": ("c.md", SAMPLE.encode(), "text/markdown")})
    assert res.status_code == 403


def test_extract_needs_teacher(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    client.put(f"/api/classes/{klass['seq']}/roster", json={"join_mode": "OPEN", "roster": []}, headers=teacher)
    joined = client.post("/api/enrollments", json={"invite_code": klass["invite_code"], "student_no": "20260001"})
    student = bearer(joined.json()["access_token"])
    res = client.post(f"/api/classes/{klass['seq']}/assignments/extract", headers=student,
                      files={"file": ("c.md", SAMPLE.encode(), "text/markdown")})
    assert res.status_code == 403


def test_sample_draft(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    res = client.post(f"/api/classes/{klass['seq']}/assignments/drafts", json={"source": "SAMPLE"}, headers=teacher)
    assert res.status_code == 200 and res.json()["seq"] is None
    assert res.json()["title"].startswith("2진수") and len(res.json()["questions"]) == 5


def test_preview_and_prompt_draft(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    draft = client.post(f"/api/classes/{klass['seq']}/assignments/drafts", json={"source": "SAMPLE"},
                        headers=teacher).json()
    preview = client.post("/api/assignments/preview", json=draft, headers=teacher)
    assert preview.status_code == 200
    body = preview.json()
    assert body["hint_mode_label"] and body["lines"][0].startswith("문항 5개")
    prompt = client.post("/api/assignments/prompt-draft", json=draft, headers=teacher)
    assert prompt.status_code == 200
    text = prompt.json()["prompt"]
    assert "2진수 변환기" in text and "문항 5 (간단 제작)" in text
    # 지시문 초안에 정답 · 숨김 테스트 · 모범 답안은 들어가지 않는다
    for secret in ("11110100001001000000", "bits[33]", "자리값을 왼쪽부터"):
        assert secret not in text
