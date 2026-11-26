"""샘플 C 과제(docs/spec/samples/c-binary-assignment.md) 모양으로 저장 → 배포 → 학생 조회. 정답 누출(I8)."""

from fastapi.testclient import TestClient

from tests.factories import api_class, api_teacher, bearer

SECRETS = ["SECRET-ANSWER", "SECRET-ACCEPT", "SECRET-MISCONCEPTION", "SECRET-HIDDEN-IN", "SECRET-HIDDEN-OUT",
           "SECRET-RUBRIC", "SECRET-MODEL", "SECRET-VARIANT"]

ASSIGNMENT = {
    "title": "2진수 변환기 · 덧셈기 · 뺄셈기", "course": "프로그래밍 기초", "audience": "1학년", "language": "C",
    "description": "2진수를 문자열로 다룬다.",
    "questions": [
        {"type": "MULTIPLE_CHOICE", "points": 10, "prompt": "1011은?", "choices": ["11", "13", "1011", "3"],
         "answer": "0", "misconceptions": {"1": "SECRET-MISCONCEPTION"},
         "variant": {"type": "MULTIPLE_CHOICE", "prompt": "SECRET-VARIANT 1101은?", "choices": ["13", "11"],
                     "answer": "0"}},
        {"type": "SHORT_ANSWER", "points": 10, "prompt": "출력은?", "code": "printf(\"%d\", 13);",
         "answer": "SECRET-ANSWER", "accepted_answers": ["SECRET-ACCEPT"]},
        {"type": "CODE", "points": 20, "prompt": "변환기", "starter_code": "void print_binary(unsigned n) {}",
         "tests": [{"input": "5", "expected_output": "101"},
                   {"input": "SECRET-HIDDEN-IN", "expected_output": "SECRET-HIDDEN-OUT", "hidden": True}],
         "model_answer": "SECRET-MODEL"},
        {"type": "PROJECT", "points": 35, "prompt": "뺄셈기", "rubric": ["SECRET-RUBRIC"], "ai_help": True},
    ],
}


def _approved_student(client: TestClient, teacher: dict[str, str], klass: dict) -> dict[str, str]:
    body = {"join_mode": "OPEN", "roster": []}
    client.put(f"/api/classes/{klass['seq']}/roster", json=body, headers=teacher)
    joined = client.post("/api/enrollments", json={"invite_code": klass["invite_code"], "student_no": "20260001"})
    return bearer(joined.json()["access_token"])


def test_save_publish_and_student_sees_no_secrets(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    created = client.post(f"/api/classes/{klass['seq']}/assignments", json=ASSIGNMENT, headers=teacher)
    assert created.status_code == 201, created.text
    aid = created.json()["seq"]

    full = client.get(f"/api/assignments/{aid}", headers=teacher).text
    assert all(secret in full for secret in SECRETS)  # 교수자는 모두 본다

    student = _approved_student(client, teacher, klass)
    assert client.get(f"/api/assignments/{aid}/solve", headers=student).status_code == 403  # 아직 초안
    published = client.post(f"/api/assignments/{aid}/publish", headers=teacher)
    assert published.json() == {"invite_code": klass["invite_code"]}

    solve = client.get(f"/api/assignments/{aid}/solve", headers=student)
    assert solve.status_code == 200
    assert not [secret for secret in SECRETS if secret in solve.text]  # I8: 하나도 없어야 한다
    code = solve.json()["questions"][2]
    assert code["public_tests"] == [{"input": "5", "expected_output": "101"}] and code["hidden_test_count"] == 1


def test_published_questions_locked_over_api(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    aid = client.post(f"/api/classes/{klass['seq']}/assignments", json=ASSIGNMENT, headers=teacher).json()["seq"]
    client.post(f"/api/assignments/{aid}/publish", headers=teacher)
    current = client.get(f"/api/assignments/{aid}", headers=teacher).json()
    same = client.put(f"/api/assignments/{aid}", json={**current, "title": "제목만 바꿈"}, headers=teacher)
    assert same.status_code == 200 and same.json()["title"] == "제목만 바꿈"
    changed = {**current, "questions": current["questions"][:2]}
    res = client.put(f"/api/assignments/{aid}", json=changed, headers=teacher)
    assert res.status_code == 409 and res.json()["code"] == "CONFLICT"


def test_draft_list_and_release(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    draft = client.post(f"/api/classes/{klass['seq']}/assignments/drafts", json={"source": "BLANK"}, headers=teacher)
    assert draft.status_code == 200 and draft.json()["seq"] is None and draft.json()["language"] == "C"
    assert client.post(f"/api/classes/{klass['seq']}/assignments/drafts", json={"source": "UNKNOWN"},
                       headers=teacher).status_code == 400  # SAMPLE은 test_assignment_md.py
    aid = client.post(f"/api/classes/{klass['seq']}/assignments", json=ASSIGNMENT, headers=teacher).json()["seq"]
    assert client.post(f"/api/assignments/{aid}/release", headers=teacher).status_code == 409
    client.post(f"/api/assignments/{aid}/publish", headers=teacher)
    assert client.post(f"/api/assignments/{aid}/release", headers=teacher).json() == {"results_released": True}
    summary = client.get(f"/api/classes/{klass['seq']}/assignments", headers=teacher).json()[0]
    assert summary["results_released"] is True and summary["status"] == "OPEN"


def test_permissions(client: TestClient):
    owner = api_teacher(client, "a@example.test")
    other = api_teacher(client, "b@example.test")
    klass = api_class(client, owner)
    aid = client.post(f"/api/classes/{klass['seq']}/assignments", json=ASSIGNMENT, headers=owner).json()["seq"]
    assert client.get(f"/api/assignments/{aid}", headers=other).status_code == 403
    assert client.get(f"/api/assignments/{aid}").status_code == 401
    student = _approved_student(client, owner, klass)
    assert client.get(f"/api/assignments/{aid}", headers=student).status_code == 403  # 학생은 교수자 조회 불가
    assert client.get(f"/api/assignments/{aid}/solve", headers=owner).status_code == 403  # 교수자는 학생 조회 불가


def test_invalid_question_is_400(client: TestClient):
    teacher = api_teacher(client)
    klass = api_class(client, teacher)
    bad = {**ASSIGNMENT, "questions": [{**ASSIGNMENT["questions"][0], "answer": "9"}]}
    res = client.post(f"/api/classes/{klass['seq']}/assignments", json=bad, headers=teacher)
    assert res.status_code == 400 and res.json()["code"] == "VALIDATION_FAILED"
