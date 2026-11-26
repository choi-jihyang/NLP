"""간단 제작 채점 — 목록 · 점수 범위 · 남의 클래스(I7) · 참고 신호(붙여넣기 길이만)."""

from fastapi.testclient import TestClient

from tests.factories import api_teacher
from tests.test_submissions import setup, submit


def _project_answer(client, teacher, student, aid, qids):
    project = qids[3]
    submit(client, student, aid, project, "int main(void){ /* 빌림 방식 */ return 0; }")
    client.post("/api/paste-events", headers=student, json={"question_id": project, "field": "ANSWER",
                                                            "length": 640, "pasted_at": "2026-11-25T23:00:00+09:00"})
    items = client.get(f"/api/assignments/{aid}/grading", headers=teacher).json()
    return items


def test_list_shows_submitted_project_answers_with_signals(client: TestClient):
    teacher, student, aid, qids = setup(client, policy={"concept_check_enabled": False})
    items = _project_answer(client, teacher, student, aid, qids)
    assert len(items) == 1
    item = items[0]
    assert (item["student_name"], item["question_index"], item["points"]) == ("20260001", 3, 35)
    assert item["rubric"] == ["빌림 처리"] and item["score"] is None and "빌림 방식" in item["content"]
    assert item["signals"] == ["답 칸에 640자를 한 번에 붙여넣음"]


def test_grade_sets_score_and_feedback_within_points(client: TestClient):
    teacher, student, aid, qids = setup(client, policy={"concept_check_enabled": False})
    answer_id = _project_answer(client, teacher, student, aid, qids)[0]["answer_id"]
    assert client.put(f"/api/answers/{answer_id}/grade", json={"score": 36}, headers=teacher).status_code == 400
    assert client.put(f"/api/answers/{answer_id}/grade", json={"score": -1}, headers=teacher).status_code == 400
    res = client.put(f"/api/answers/{answer_id}/grade", json={"score": 30, "feedback": "음수 처리 좋아요"},
                     headers=teacher)
    assert res.status_code == 200 and res.json()["score"] == 30 and res.json()["feedback"] == "음수 처리 좋아요"
    assert client.get(f"/api/assignments/{aid}/grading", headers=teacher).json()[0]["score"] == 30


def test_grading_is_teacher_own_class_only(client: TestClient):
    teacher, student, aid, qids = setup(client, policy={"concept_check_enabled": False})
    answer_id = _project_answer(client, teacher, student, aid, qids)[0]["answer_id"]
    other = api_teacher(client, email="other@example.test")
    assert client.get(f"/api/assignments/{aid}/grading", headers=other).status_code == 403
    assert client.put(f"/api/answers/{answer_id}/grade", json={"score": 1}, headers=other).status_code == 403
    assert client.put(f"/api/answers/{answer_id}/grade", json={"score": 1}, headers=student).status_code == 403
    assert client.put("/api/answers/99999/grade", json={"score": 1}, headers=teacher).status_code == 404


def test_only_submitted_project_answers_can_be_graded(client: TestClient, db):
    from sqlalchemy import select

    from app.models import Answer

    teacher, student, aid, qids = setup(client, policy={"concept_check_enabled": False})
    submit(client, student, aid, qids[0], "0")
    assert client.get(f"/api/assignments/{aid}/grading", headers=teacher).json() == []  # 객관식은 목록에 없음
    mc = db.scalar(select(Answer).where(Answer.question_id == qids[0]))
    assert client.put(f"/api/answers/{mc.seq}/grade", json={"score": 1}, headers=teacher).status_code == 409
