"""이해 확인 · 반 리포트 · 학생별 기록 · 내 리포트 — 결과 공개 전 비공개 · 권한(I7) · 규칙 기반 문장."""

from fastapi.testclient import TestClient

from tests.factories import api_teacher, bearer
from tests.test_submissions import ASSIGNMENT, TO_BINARY, needs_gcc, runner, submit  # noqa: F401  (fixture)
from tests.test_submissions import setup as base_setup

MC_VARIANT = {"type": "MULTIPLE_CHOICE", "prompt": "1101은?", "choices": ["13", "11"], "answer": "0"}
SA_VARIANT = {"type": "SHORT_ANSWER", "prompt": "n=6이면?", "answer": "0110"}
WITH_VARIANTS = {
    **ASSIGNMENT,
    "policy": {"concept_check_enabled": False, "variant_enabled": True},
    "questions": [
        {**ASSIGNMENT["questions"][0], "misconceptions": {"1": "자리값을 왼쪽부터 읽음"}, "variant": MC_VARIANT},
        {**ASSIGNMENT["questions"][1], "variant": SA_VARIANT},
        *ASSIGNMENT["questions"][2:],
    ],
}


def setup(client, monkeypatch=None):
    import tests.test_submissions as ts

    original = ts.ASSIGNMENT
    ts.ASSIGNMENT = WITH_VARIANTS
    try:
        return base_setup(client)
    finally:
        ts.ASSIGNMENT = original


def finish(client, student, aid, qids, mc="1", sa="1101"):
    for qid, content in zip(qids, [mc, sa, TO_BINARY, "int main(void){return 0;}"], strict=True):
        submit(client, student, aid, qid, content)
    assert client.post(f"/api/assignments/{aid}/submission/finalize", headers=student).status_code == 200


def check(client, student, aid, qids, mc="1", sa="0110", conf="SURE"):
    body = {"explanation": "자리값을 곱해 더했어요", "answers": [
        {"question_id": qids[0], "value": mc, "confidence": conf},
        {"question_id": qids[1], "value": sa, "confidence": "UNSURE"},
    ]}
    return client.post(f"/api/assignments/{aid}/understanding-check", json=body, headers=student)


# ---- 이해 확인 ----


@needs_gcc
def test_understanding_check_only_after_finalize_and_hides_answers(client: TestClient, runner):  # noqa: F811
    _, student, aid, qids = setup(client)
    assert client.get(f"/api/assignments/{aid}/understanding-check", headers=student).status_code == 409
    finish(client, student, aid, qids)
    res = client.get(f"/api/assignments/{aid}/understanding-check", headers=student)
    assert res.status_code == 200
    body = res.json()
    assert [i["question_id"] for i in body["items"]] == qids[:2]
    assert "0110" not in res.text and '"answer"' not in res.text  # 정답 없음
    assert "print" in body["explain_code"] or "putchar" in body["explain_code"]  # 내 코드
    receipt = check(client, student, aid, qids)
    assert receipt.status_code == 200 and set(receipt.json()) == {"submitted_at"}  # 정오 없음
    assert check(client, student, aid, qids).status_code == 409  # 한 번만


@needs_gcc
def test_understanding_check_rejects_unknown_question(client: TestClient, runner):  # noqa: F811
    _, student, aid, qids = setup(client)
    finish(client, student, aid, qids)
    body = {"answers": [{"question_id": qids[2], "value": "x"}]}
    assert client.post(f"/api/assignments/{aid}/understanding-check", json=body,
                       headers=student).status_code == 400


# ---- 반 리포트 ----


@needs_gcc
def test_assignment_report_numbers_and_misconception_rows(client: TestClient, runner):  # noqa: F811
    teacher, student, aid, qids = setup(client)
    finish(client, student, aid, qids, mc="1")  # 오개념 선택지
    check(client, student, aid, qids, mc="1", sa="0110")
    res = client.get(f"/api/assignments/{aid}/report", headers=teacher)
    assert res.status_code == 200, res.text
    r = res.json()
    assert (r["submitted_count"], r["student_count"]) == (1, 1)
    assert r["alone_variant_rate"] == 50  # 확인 문제 2개 중 1개
    mc = next(m for m in r["mistakes"] if m["question_index"] == 0)
    assert mc["kind"] == "CHOICE"
    picked = next(row for row in mc["rows"] if row["rate"] == 100)
    assert picked["note"] == "자리값을 왼쪽부터 읽음" and picked["correct"] is False
    assert r["supplement"]["question_index"] == 0 and "자리값" in r["supplement"]["summary"]
    assert [s["question_index"] for s in r["question_stats"]] == [0, 1, 2, 3]
    # 확인 문제가 없는 문항(코드 작성 · 간단 제작)은 0%가 아니라 null
    assert [s["variant_rate"] for s in r["question_stats"]] == [0, 100, None, None]


def test_report_is_teacher_own_class_only(client: TestClient):
    teacher, student, aid, _ = setup(client)
    other = api_teacher(client, email="o@example.test")
    assert client.get(f"/api/assignments/{aid}/report", headers=other).status_code == 403
    assert client.get(f"/api/assignments/{aid}/report", headers=student).status_code == 403


# ---- 학생별 기록 ----


@needs_gcc
def test_student_record(client: TestClient, db, runner):  # noqa: F811
    from sqlalchemy import select

    from app.models import Answer, Enrollment

    teacher, student, aid, qids = setup(client)
    finish(client, student, aid, qids, mc="0")
    a = db.scalar(select(Answer).where(Answer.question_id == qids[0]))
    a.hint_step = 2
    db.commit()
    check(client, student, aid, qids, mc="1")
    sid = db.scalar(select(Enrollment)).student_id
    res = client.get(f"/api/assignments/{aid}/students/{sid}/record", headers=teacher)
    assert res.status_code == 200, res.text
    r = res.json()
    assert r["student_name"] == "20260001" and r["max_score"] == 75 and r["pending_points"] == 35
    assert r["score"] == 40 and r["variant_total"] == 2 and r["variant_passed"] == 1
    assert r["rows"][0]["variant"] == "오답 (1)" and r["rows"][2]["result"] == "테스트 4/4 통과"
    assert "문항 1" in r["variant_note"]
    assert client.get(f"/api/assignments/{aid}/students/99999/record", headers=teacher).status_code == 404


# ---- 내 리포트 ----


@needs_gcc
def test_my_report_hidden_until_release_then_shows_results(client: TestClient, runner):  # noqa: F811
    teacher, student, aid, qids = setup(client)
    finish(client, student, aid, qids, mc="1")
    check(client, student, aid, qids, mc="1", conf="SURE")
    before = client.get(f"/api/assignments/{aid}/my-report", headers=student)
    assert before.json() == {"released": False, "assignment_title": "2진수"}
    client.post(f"/api/assignments/{aid}/release", headers=teacher)
    r = client.get(f"/api/assignments/{aid}/my-report", headers=student).json()
    assert r["released"] is True and r["score"] == 30 and r["max_score"] == 75 and r["pending_points"] == 35
    assert r["misconceptions"] == ["문항 1: 자리값을 왼쪽부터 읽음"]
    assert r["overconfident"] == ["문항 1 확인 문제"]
    assert r["questions"][0]["correct_answer"] == "① 11"
    statuses = {c["name"]: c["status"] for c in r["concepts"]}
    assert statuses["문항 1 (객관식 퀴즈)"] == "NEEDS_WORK" and statuses["문항 2 (출력 예측)"] == "CONFIRMED"
    assert any(s.startswith("문항 1 다시 보기") for s in r["next_steps"])


def test_my_report_other_class_forbidden(client: TestClient):
    teacher, _, aid, _ = setup(client)
    other = api_teacher(client, email="z@example.test")
    from tests.factories import api_class

    k = api_class(client, other, name="Z")
    client.put(f"/api/classes/{k['seq']}/roster", json={"join_mode": "OPEN", "roster": []}, headers=other)
    outsider = bearer(client.post("/api/enrollments", json={"invite_code": k["invite_code"], "student_no": "9"})
                      .json()["access_token"])
    assert client.get(f"/api/assignments/{aid}/my-report", headers=outsider).status_code == 403
