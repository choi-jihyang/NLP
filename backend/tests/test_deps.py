from datetime import timedelta
from typing import Annotated

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_student, require_teacher
from app.api.errors import install_error_handling
from app.core.clock import now_kst
from app.core.enums import Role
from app.core.tokens import issue_token
from app.db.session import get_db
from app.models import User
from tests.conftest import TEST_JWT_SECRET


@pytest.fixture
def api(db: Session) -> TestClient:
    app = FastAPI()
    install_error_handling(app)

    @app.get("/me")
    def me(user: Annotated[User, Depends(get_current_user)]) -> dict[str, int]:
        return {"seq": user.seq}

    @app.get("/teacher/{class_id}")
    def teacher_only(class_id: int, user: Annotated[User, Depends(require_teacher)]) -> dict[str, int]:
        return {"class_id": class_id, "seq": user.seq}

    @app.get("/student")
    def student_only(user: Annotated[User, Depends(require_student)]) -> dict[str, int]:
        return {"seq": user.seq}

    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


def _user(db: Session, role: Role) -> User:
    user = User(role=role, name="u", email=None)
    db.add(user)
    db.commit()
    return user


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _token(user: User) -> str:
    return issue_token(user, now_kst() + timedelta(hours=1))


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer not-a-token"}])
def test_missing_or_malformed_header_is_401(api: TestClient, headers: dict[str, str]):
    res = api.get("/me", headers=headers)
    assert res.status_code == 401
    assert res.json()["code"] == "UNAUTHORIZED"


def test_expired_token_is_401(api: TestClient, db: Session):
    user = _user(db, Role.TEACHER)
    res = api.get("/me", headers=_bearer(issue_token(user, now_kst() - timedelta(seconds=1))))
    assert res.status_code == 401


def test_deleted_user_is_401(api: TestClient):
    ghost = User(seq=999, role=Role.TEACHER, name="ghost")
    res = api.get("/me", headers=_bearer(_token(ghost)))
    assert res.status_code == 401


def test_teacher_route(api: TestClient, db: Session):
    teacher = _user(db, Role.TEACHER)
    res = api.get("/teacher/3", headers=_bearer(_token(teacher)))
    assert res.status_code == 200
    assert res.json() == {"class_id": 3, "seq": teacher.seq}


def test_student_token_on_teacher_route_is_403(api: TestClient, db: Session):
    student = _user(db, Role.STUDENT)
    res = api.get("/teacher/3", headers=_bearer(_token(student)))
    assert res.status_code == 403
    assert res.json()["code"] == "FORBIDDEN"


def test_teacher_token_on_student_route_is_403(api: TestClient, db: Session):
    teacher = _user(db, Role.TEACHER)
    assert api.get("/student", headers=_bearer(_token(teacher))).status_code == 403


def test_db_role_wins_over_token_role(api: TestClient, db: Session):
    student = _user(db, Role.STUDENT)
    now = int(now_kst().timestamp())
    forged = jwt.encode(
        {"sub": str(student.seq), "role": "TEACHER", "iat": now, "exp": now + 3600}, TEST_JWT_SECRET, algorithm="HS256"
    )
    assert api.get("/teacher/3", headers=_bearer(forged)).status_code == 403


def test_non_numeric_path_id_is_400(api: TestClient, db: Session):
    teacher = _user(db, Role.TEACHER)
    res = api.get("/teacher/abc", headers=_bearer(_token(teacher)))
    assert res.status_code == 400
    assert res.json()["code"] == "VALIDATION_FAILED"
