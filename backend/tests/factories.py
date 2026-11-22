"""테스트용 행 만들기와 API 헬퍼. 운영 코드에서 import하지 않는다."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.enums import EnrollmentStatus, JoinMode, PlanCode, Role
from app.models import ClassMember, ClassRoom, Enrollment, User


def make_teacher(db: Session, email: str = "t@example.test") -> User:
    user = User(role=Role.TEACHER, email=email, password_hash="x", name="교수")
    db.add(user)
    db.flush()
    return user


def make_student(db: Session, name: str = "20260001") -> User:
    user = User(role=Role.STUDENT, name=name)
    db.add(user)
    db.flush()
    return user


def make_class(
    db: Session,
    teacher: User,
    *,
    code: str = "TG-1000",
    limit: int = 50,
    join_mode: JoinMode = JoinMode.APPROVAL,
    starts_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> ClassRoom:
    start = starts_at or now_kst() - timedelta(days=1)
    klass = ClassRoom(
        teacher_id=teacher.seq, name="1분반", invite_code=code, plan=PlanCode.SMALL, student_limit=limit,
        join_mode=join_mode, starts_at=start, expires_at=expires_at or start + timedelta(days=365),
    )
    db.add(klass)
    db.flush()
    return klass


def enroll(
    db: Session,
    klass: ClassRoom,
    student: User,
    student_no: str,
    status: EnrollmentStatus = EnrollmentStatus.APPROVED,
    decided: bool | None = None,
) -> Enrollment:
    """decided가 None이면 APPROVED일 때만 decided_at을 채운다."""
    has_decision = status == EnrollmentStatus.APPROVED if decided is None else decided
    enrollment = Enrollment(
        class_id=klass.seq, student_id=student.seq, student_no=student_no, status=status,
        decided_at=now_kst() if has_decision else None,
    )
    db.add(enrollment)
    db.flush()
    return enrollment


def add_member(db: Session, klass: ClassRoom, student_no: str, is_use: bool = True) -> ClassMember:
    member = ClassMember(class_id=klass.seq, student_no=student_no, is_use=is_use)
    db.add(member)
    db.flush()
    return member


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def api_teacher(client: TestClient, email: str = "teacher@example.test") -> dict[str, str]:
    res = client.post("/api/auth/signup", json={"name": "김교수", "email": email, "password": "correct-horse"})
    assert res.status_code == 201, res.text
    return bearer(res.json()["access_token"])


def api_class(client: TestClient, headers: dict[str, str], name: str = "1분반") -> dict[str, object]:
    pay = client.post("/api/payments", json={"plan": "SMALL", "kind": "NEW"}, headers=headers)
    assert pay.status_code == 201, pay.text
    body = {"name": name, "starts_on": now_kst().date().isoformat(), "payment_seq": pay.json()["payment_seq"]}
    res = client.post("/api/classes", json=body, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()
