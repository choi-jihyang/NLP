from datetime import timedelta

import pytest
from sqlalchemy import Engine, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import KST, now_kst, start_of_day_kst
from app.core.enums import EnrollmentStatus, PlanCode, Role
from app.models import ClassMember, ClassRoom, Enrollment, User
from app.schemas.ai_policy import default_ai_policy


def _teacher(db: Session) -> User:
    t = User(role=Role.TEACHER, email="t@example.test", password_hash="x", name="교수")
    db.add(t)
    db.flush()
    return t


def _class(db: Session, teacher: User, code: str = "TG-1000") -> ClassRoom:
    start = start_of_day_kst(now_kst().date())
    c = ClassRoom(
        teacher_id=teacher.id, name="1분반", invite_code=code, plan=PlanCode.SMALL,
        student_limit=50, starts_at=start, expires_at=start + timedelta(days=365),
    )
    db.add(c)
    db.flush()
    return c


def _student(db: Session, no: str) -> User:
    s = User(role=Role.STUDENT, name=no)
    db.add(s)
    db.flush()
    return s


def test_init_db_creates_five_tables(db: Session):
    bind = db.get_bind()
    assert isinstance(bind, Engine)
    assert {"users", "classes", "class_payments", "enrollments", "class_members"} <= set(
        inspect(bind).get_table_names()
    )


def test_class_defaults(db: Session):
    c = _class(db, _teacher(db))
    db.commit()
    db.expire_all()  # 메모리 객체가 아니라 DB에서 다시 읽는다
    loaded = db.scalar(select(ClassRoom).where(ClassRoom.id == c.id))
    assert loaded is not None
    assert loaded.join_mode == "APPROVAL"
    assert loaded.ai_defaults == default_ai_policy()
    assert loaded.created_at.tzinfo is not None
    assert loaded.created_at.utcoffset() == timedelta(hours=9)
    assert loaded.starts_at.tzinfo == KST


def test_updated_at_changes_on_update(db: Session):
    t = _teacher(db)
    db.commit()
    before = t.updated_at
    t.name = "새 이름"
    db.commit()
    assert t.updated_at > before


def test_many_students_without_email(db: Session):
    _student(db, "20260001")
    _student(db, "20260002")
    db.commit()
    assert len(db.scalars(select(User).where(User.email.is_(None))).all()) == 2


def test_same_student_no_twice_in_one_class_rejected(db: Session):
    c = _class(db, _teacher(db))
    db.add(Enrollment(class_id=c.id, student_id=_student(db, "a").id, student_no="20260001",
                      status=EnrollmentStatus.APPROVED))
    db.add(Enrollment(class_id=c.id, student_id=_student(db, "b").id, student_no="20260001",
                      status=EnrollmentStatus.PENDING))
    with pytest.raises(IntegrityError):
        db.commit()


def test_same_student_no_in_two_classes_allowed(db: Session):
    t = _teacher(db)
    c1, c2 = _class(db, t, "TG-1001"), _class(db, t, "TG-1002")
    s = _student(db, "20260001")
    for c in (c1, c2):
        db.add(Enrollment(class_id=c.id, student_id=s.id, student_no="20260001", status=EnrollmentStatus.APPROVED))
    db.commit()


def test_class_member_unique_and_default_is_use(db: Session):
    c = _class(db, _teacher(db))
    m = ClassMember(class_id=c.id, student_no="20260001")
    db.add(m)
    db.commit()
    assert m.is_use is True
    db.add(ClassMember(class_id=c.id, student_no="20260001"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_foreign_key_enforced(db: Session):
    db.add(Enrollment(class_id=999, student_id=_student(db, "x").id, student_no="20260009",
                      status=EnrollmentStatus.PENDING))
    with pytest.raises(IntegrityError):
        db.commit()
