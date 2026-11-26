"""⑦ 풀이 · 제출: 공개 테스트 실행 · 자동 채점 · 개념 확인 · 최종 제출 · 결과 공개 전 비공개 · 권한(I7).

코드 작성 채점은 Docker 없이 sandbox/harness.py를 직접 쓰는 LocalRunner로 돈다(gcc 필요, 없으면 건너뜀).
"""

import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.enums import Language
from app.runner.base import CodeRunner, IOCase, RunnerUnavailableError, RunResult
from tests.factories import api_class, api_teacher, bearer

HARNESS = Path(__file__).resolve().parents[1] / "sandbox" / "harness.py"
needs_gcc = pytest.mark.skipif(not shutil.which("gcc"), reason="gcc 없음")


class LocalRunner(CodeRunner):
    """테스트 전용: 컨테이너 없이 harness를 바로 실행한다(신뢰된 테스트 코드만)."""

    def __init__(self) -> None:
        self.calls: list[list[IOCase]] = []

    async def run(self, language: Language, code: str, tests: list[IOCase]) -> RunResult:
        self.calls.append(list(tests))
        payload = {"language": language.value, "code": code, "tests": [t.model_dump() for t in tests], "timeout": 5}
        proc = await asyncio.to_thread(
            subprocess.run, [sys.executable, "-I", str(HARNESS)], input=json.dumps(payload),
            capture_output=True, text=True, timeout=60,
        )
        return RunResult.model_validate(json.loads(proc.stdout.strip().splitlines()[-1]))


class DownRunner(CodeRunner):
    async def run(self, language, code, tests):  # noqa: ANN001, ANN201
        raise RunnerUnavailableError("docker 꺼짐")


TO_BINARY = (
    "#include <stdio.h>\nint main(void){ unsigned n; scanf(\"%u\", &n); char b[40]; int i = 0;\n"
    "  if (n == 0) { puts(\"0\"); return 0; }\n  while (n > 0) { b[i++] = '0' + n % 2; n /= 2; }\n"
    "  while (i > 0) putchar(b[--i]); putchar('\\n'); return 0; }\n"
)
ONLY_PUBLIC = '#include <stdio.h>\nint main(void){ unsigned n; scanf("%u", &n); puts(n==5?"101":n==0?"0":"?"); }\n'

ASSIGNMENT = {
    "title": "2진수", "language": "C",
    "policy": {"concept_check_enabled": True, "hint_penalty": "NONE"},
    "questions": [
        {"type": "MULTIPLE_CHOICE", "points": 10, "prompt": "1011은?", "choices": ["11", "13"], "answer": "0"},
        {"type": "SHORT_ANSWER", "points": 10, "prompt": "출력은?", "answer": "1101", "accepted_answers": ["1 1 0 1"]},
        {"type": "CODE", "points": 20, "prompt": "변환기",
         "tests": [{"input": "5\n", "expected_output": "101"}, {"input": "0\n", "expected_output": "0"},
                   {"input": "255\n", "expected_output": "11111111", "hidden": True},
                   {"input": "8\n", "expected_output": "1000", "hidden": True}]},
        {"type": "PROJECT", "points": 35, "prompt": "뺄셈기", "rubric": ["빌림 처리"]},
    ],
}
LOCKED_FIELDS = ("is_correct", "score", "test_results", "feedback", "expected_output\": \"11111111")


@pytest.fixture
def runner(monkeypatch):
    r = LocalRunner()
    monkeypatch.setattr("app.api.routes.submissions.get_code_runner", lambda: r)
    return r


def setup(client: TestClient, policy: dict | None = None, due_at: str | None = None):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    body = {**ASSIGNMENT, "policy": {**ASSIGNMENT["policy"], **(policy or {})}, "due_at": due_at}
    aid = client.post(f"/api/classes/{klass['seq']}/assignments", json=body, headers=teacher).json()["seq"]
    client.post(f"/api/assignments/{aid}/publish", headers=teacher)
    client.put(f"/api/classes/{klass['seq']}/roster", json={"join_mode": "OPEN", "roster": []}, headers=teacher)
    joined = client.post("/api/enrollments", json={"invite_code": klass["invite_code"], "student_no": "20260001"})
    student = bearer(joined.json()["access_token"])
    qids = [q["seq"] for q in client.get(f"/api/assignments/{aid}", headers=teacher).json()["questions"]]
    return teacher, student, aid, qids


def base(aid):
    return f"/api/assignments/{aid}"


def submit(client, student, aid, qid, content):
    return client.put(f"{base(aid)}/answers/{qid}", json={"content": content}, headers=student)


def concept(client, student, aid, qid, reply="append는 리스트 끝에 붙여요"):
    return client.post(f"{base(aid)}/answers/{qid}/concept-check", json={"reply": reply, "elapsed_ms": 4200},
                       headers=student)


# ---- 조회 · 실행 ----


def test_get_submission_creates_empty(client: TestClient):
    _, student, aid, _ = setup(client)
    res = client.get(f"{base(aid)}/submission", headers=student)
    assert res.status_code == 200
    assert res.json() == {"assignment_id": aid, "answers": {}, "finalized": False, "results_released": False}


@needs_gcc
def test_run_uses_public_tests_only(client: TestClient, runner):
    _, student, aid, qids = setup(client)
    res = client.post(f"{base(aid)}/questions/{qids[2]}/run", json={"code": TO_BINARY}, headers=student)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ok"] and [r["passed"] for r in body["results"]] == [True, True]
    assert "11111111" not in res.text  # 숨김 기대 출력 없음
    assert [t.input for t in runner.calls[-1]] == ["5\n", "0\n"]


@needs_gcc
def test_run_reports_compile_error(client: TestClient, runner):
    _, student, aid, qids = setup(client)
    body = client.post(f"{base(aid)}/questions/{qids[2]}/run", json={"code": "int main( {"}, headers=student).json()
    assert body["ok"] is False and body["error"].startswith("컴파일 오류")


def test_run_only_for_code_questions_and_503_when_runner_down(client: TestClient, monkeypatch):
    _, student, aid, qids = setup(client)
    assert client.post(f"{base(aid)}/questions/{qids[0]}/run", json={"code": "x"}, headers=student).status_code == 409
    monkeypatch.setattr("app.api.routes.submissions.get_code_runner", lambda: DownRunner())
    res = client.post(f"{base(aid)}/questions/{qids[2]}/run", json={"code": "x"}, headers=student)
    assert res.status_code == 503 and res.json()["code"] == "RUNNER_UNAVAILABLE"


# ---- 제출 · 채점 ----


@needs_gcc
def test_grading_is_stored_but_hidden_until_release(client: TestClient, db, runner):
    from sqlalchemy import select

    from app.models import Answer

    teacher, student, aid, qids = setup(client, policy={"concept_check_enabled": False})
    assert submit(client, student, aid, qids[0], "0").status_code == 200
    assert submit(client, student, aid, qids[1], "1 1 0 1 ").status_code == 200
    res = submit(client, student, aid, qids[2], ONLY_PUBLIC)
    assert res.status_code == 200
    assert res.json()["answers"][str(qids[2])]["status"] == "SUBMITTED"
    for field in LOCKED_FIELDS:
        assert field not in res.text  # 결과 공개 전 정오 · 점수 · 숨김 테스트 결과 없음
    answers = {a.question_id: a for a in db.scalars(select(Answer))}
    assert answers[qids[0]].is_correct and answers[qids[0]].score == 10
    assert answers[qids[1]].is_correct and answers[qids[1]].score == 10
    code = answers[qids[2]]
    assert code.is_correct is False and code.score == 10  # 4개 중 2개 통과 → 20 × 2/4
    assert [r["hidden"] for r in code.test_results] == [False, False, True, True]


@needs_gcc
def test_full_marks_and_hint_penalty(client: TestClient, db, runner):
    from sqlalchemy import select

    from app.models import Answer

    _, student, aid, qids = setup(client, policy={"concept_check_enabled": False, "hint_penalty": "PER_STEP"})
    submit(client, student, aid, qids[2], TO_BINARY)
    answer = db.scalar(select(Answer).where(Answer.question_id == qids[2]))
    assert answer.is_correct and answer.score == 20
    answer.hint_step = 2
    db.commit()
    submit(client, student, aid, qids[2], TO_BINARY)
    db.refresh(answer)
    assert answer.score == 18 and answer.submit_count == 2


def test_wrong_choice_format_is_rejected(client: TestClient, runner):
    _, student, aid, qids = setup(client)
    assert submit(client, student, aid, qids[0], "13").status_code == 400


def test_runner_down_on_submit_is_503_and_nothing_saved(client: TestClient, monkeypatch):
    _, student, aid, qids = setup(client)
    monkeypatch.setattr("app.api.routes.submissions.get_code_runner", lambda: DownRunner())
    assert submit(client, student, aid, qids[2], TO_BINARY).status_code == 503
    assert client.get(f"{base(aid)}/submission", headers=student).json()["answers"].get(str(qids[2]), {}).get(
        "submit_count", 0) == 0


# ---- 개념 확인 ----


def test_first_solo_submit_needs_concept_check_then_submitted(client: TestClient, runner):
    _, student, aid, qids = setup(client)
    state = submit(client, student, aid, qids[0], "0").json()["answers"][str(qids[0])]
    assert state["status"] == "AWAITING_CHECK"
    assert state["concept_check"]["answered"] == 0 and len(state["concept_check"]["questions"]) == 1
    done = concept(client, student, aid, qids[0]).json()["answers"][str(qids[0])]
    assert done["status"] == "SUBMITTED" and done["concept_check"]["answered"] == 1
    # 다시 제출하면 개념 확인 없이 SUBMITTED
    again = submit(client, student, aid, qids[0], "1").json()["answers"][str(qids[0])]
    assert again["status"] == "SUBMITTED" and again["submit_count"] == 2


def test_cancel_concept_check_returns_to_draft_and_same_question_continues(client: TestClient, runner):
    _, student, aid, qids = setup(client)
    submit(client, student, aid, qids[0], "0")
    back = client.delete(f"{base(aid)}/answers/{qids[0]}/concept-check", headers=student)
    assert back.json()["answers"][str(qids[0])]["status"] == "DRAFT"
    again = submit(client, student, aid, qids[0], "0").json()["answers"][str(qids[0])]
    assert again["status"] == "AWAITING_CHECK" and len(again["concept_check"]["questions"]) == 1


def test_concept_check_body_rejects_pasted_field(client: TestClient, runner):
    """붙여넣기는 /paste-events로만 (I5) — 알 수 없는 필드는 거부."""
    _, student, aid, qids = setup(client)
    submit(client, student, aid, qids[0], "0")
    res = client.post(f"{base(aid)}/answers/{qids[0]}/concept-check",
                      json={"reply": "x", "elapsed_ms": 1, "pasted": True}, headers=student)
    assert res.status_code == 400


def test_concept_check_when_not_awaiting_is_conflict(client: TestClient, runner):
    _, student, aid, qids = setup(client, policy={"concept_check_enabled": False})
    submit(client, student, aid, qids[0], "0")
    assert concept(client, student, aid, qids[0]).status_code == 409


# ---- 최종 제출 ----


def _submit_all(client, student, aid, qids):
    for qid, content in zip(qids, ["0", "1101", TO_BINARY, "int main(void){return 0;}"], strict=True):
        submit(client, student, aid, qid, content)


@needs_gcc
def test_finalize_requires_all_submitted_then_locks(client: TestClient, runner):
    _, student, aid, qids = setup(client, policy={"concept_check_enabled": False})
    submit(client, student, aid, qids[0], "0")
    early = client.post(f"{base(aid)}/submission/finalize", headers=student)
    assert early.status_code == 409 and "2" in early.json()["message"]
    _submit_all(client, student, aid, qids)
    done = client.post(f"{base(aid)}/submission/finalize", headers=student)
    assert done.status_code == 200 and done.json()["finalized"] is True
    assert submit(client, student, aid, qids[0], "1").json()["code"] == "ALREADY_SUBMITTED"
    res = client.post(f"{base(aid)}/questions/{qids[2]}/run", json={"code": TO_BINARY}, headers=student)
    assert res.json()["code"] == "ALREADY_SUBMITTED"
    assert client.post(f"{base(aid)}/submission/finalize", headers=student).json()["code"] == "ALREADY_SUBMITTED"


def test_awaiting_check_blocks_finalize(client: TestClient, runner):
    _, student, aid, qids = setup(client)
    for qid in qids:
        submit(client, student, aid, qid, "0")
    assert client.post(f"{base(aid)}/submission/finalize", headers=student).status_code == 409


def test_after_due_submit_is_conflict(client: TestClient, runner):
    _, student, aid, qids = setup(client, due_at="2020-01-01T00:00:00+09:00")
    res = submit(client, student, aid, qids[0], "0")
    assert res.status_code == 409 and "마감" in res.json()["message"]


# ---- 권한 (I7) ----


def test_other_class_student_and_teacher_are_forbidden(client: TestClient, runner):
    teacher, student, aid, qids = setup(client)
    other_teacher = api_teacher(client, email="other@example.test")
    other_class = api_class(client, other_teacher, name="2분반")
    client.put(f"/api/classes/{other_class['seq']}/roster", json={"join_mode": "OPEN", "roster": []},
               headers=other_teacher)
    outsider = bearer(client.post("/api/enrollments", json={"invite_code": other_class["invite_code"],
                                                            "student_no": "99990001"}).json()["access_token"])
    assert client.get(f"{base(aid)}/submission", headers=outsider).status_code == 403
    assert submit(client, outsider, aid, qids[0], "0").status_code == 403
    assert client.get(f"{base(aid)}/submission", headers=teacher).status_code == 403  # 교수자 토큰은 학생 API 불가


def test_question_from_other_assignment_is_not_found(client: TestClient, runner):
    teacher, student, aid, qids = setup(client)
    klass_id = client.get(f"/api/assignments/{aid}", headers=teacher).json()["class_id"]
    other = client.post(f"/api/classes/{klass_id}/assignments", json=ASSIGNMENT, headers=teacher).json()
    client.post(f"/api/assignments/{other['seq']}/publish", headers=teacher)
    assert submit(client, student, aid, other["questions"][0]["seq"], "0").status_code == 404


@needs_gcc
def test_teacher_list_counts_finalized_submissions(client: TestClient, runner):
    teacher, student, aid, qids = setup(client, policy={"concept_check_enabled": False})
    klass_id = client.get(f"/api/assignments/{aid}", headers=teacher).json()["class_id"]
    count = lambda: client.get(f"/api/classes/{klass_id}/assignments", headers=teacher).json()[0]["submitted_count"]  # noqa: E731
    assert count() == 0
    _submit_all(client, student, aid, qids)
    client.post(f"{base(aid)}/submission/finalize", headers=student)
    assert count() == 1


@needs_gcc
def test_me_classes_lists_published_assignments_with_status(client: TestClient, runner):
    teacher, student, aid, qids = setup(client, policy={"concept_check_enabled": False})
    row = client.get("/api/me/classes", headers=student).json()[0]["assignments"][0]
    assert (row["seq"], row["status"], row["submitted"], row["total"], row["score_text"]) == (aid, "IN_PROGRESS", 0, 4,
                                                                                             None)
    _submit_all(client, student, aid, qids)
    client.post(f"{base(aid)}/submission/finalize", headers=student)
    assert client.get("/api/me/classes", headers=student).json()[0]["assignments"][0]["status"] == "FINALIZED"
    client.post(f"/api/assignments/{aid}/release", headers=teacher)
    row = client.get("/api/me/classes", headers=student).json()[0]["assignments"][0]
    assert row["status"] == "RELEASED" and row["score_text"].startswith("40/75점")


def test_concurrent_first_requests_do_not_500(tmp_path):
    """과제를 처음 열 때 제출 · 채팅 조회가 동시에 와도 submissions/answers UNIQUE 충돌로 500이 나지 않는다."""
    from concurrent.futures import ThreadPoolExecutor

    from sqlalchemy.orm import sessionmaker

    from app.db.init_db import init_db
    from app.db.session import create_db_engine, get_db
    from app.main import app

    engine = create_db_engine(f"sqlite:///{tmp_path / 'race.db'}")
    init_db(engine)
    make = sessionmaker(engine, expire_on_commit=False)

    def per_request():
        with make() as s:
            yield s

    app.dependency_overrides[get_db] = per_request
    try:
        client = TestClient(app, raise_server_exceptions=False)
        _, student, aid, qids = setup(client)
        urls = [f"{base(aid)}/submission"] + [f"{base(aid)}/questions/{q}/chat" for q in qids] * 2
        with ThreadPoolExecutor(8) as pool:
            codes = list(pool.map(lambda u: client.get(u, headers=student).status_code, urls))
        assert codes == [200] * len(urls)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
