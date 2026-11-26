from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import EnrollmentStatus, JoinMode
from app.models import ClassMember
from app.services.roster_service import get_roster, save_roster
from tests.factories import add_member, enroll, make_class, make_student, make_teacher


def _members(db: Session, teacher, class_id: int) -> dict[str, bool]:  # noqa: ANN001
    _, members = get_roster(db, teacher, class_id)
    return {m.student_no: m.is_use for m in members}


def test_save_roster_turns_numbers_on_and_off(db: Session):
    teacher = make_teacher(db)
    klass = make_class(db, teacher)
    add_member(db, klass, "A")
    add_member(db, klass, "B")
    mode, _ = save_roster(db, teacher, klass.seq, JoinMode.OPEN, {"A": True, "C": True, "D": False})
    assert mode == JoinMode.OPEN
    assert _members(db, teacher, klass.seq) == {"A": True, "B": False, "C": True, "D": False}


def test_duplicate_numbers_in_request_make_one_row(db: Session):
    teacher = make_teacher(db)
    klass = make_class(db, teacher)
    wanted = dict([("A", True), ("A", True)])  # 라우터가 목록을 dict로 바꿀 때 중복이 합쳐진다
    save_roster(db, teacher, klass.seq, JoinMode.APPROVAL, wanted)
    save_roster(db, teacher, klass.seq, JoinMode.APPROVAL, wanted)
    count = db.scalar(select(func.count()).select_from(ClassMember).where(ClassMember.class_id == klass.seq))
    assert count == 1


def test_save_roster_auto_approves_first_requests_only(db: Session):
    teacher = make_teacher(db)
    klass = make_class(db, teacher)
    first = enroll(db, klass, make_student(db, "A"), "A", EnrollmentStatus.PENDING)
    reentry = enroll(db, klass, make_student(db, "B"), "B", EnrollmentStatus.PENDING, decided=True)
    stranger = enroll(db, klass, make_student(db, "Z"), "Z", EnrollmentStatus.PENDING)
    save_roster(db, teacher, klass.seq, JoinMode.APPROVAL, {"A": True, "B": True})
    assert first.status == EnrollmentStatus.APPROVED and first.decided_at is not None
    assert reentry.status == EnrollmentStatus.PENDING  # 다시 입장은 명단만으로 수락하지 않는다
    assert stranger.status == EnrollmentStatus.PENDING


def test_auto_approve_respects_limit(db: Session):
    teacher = make_teacher(db)
    klass = make_class(db, teacher, limit=1)
    enroll(db, klass, make_student(db, "X"), "X")
    waiting = enroll(db, klass, make_student(db, "A"), "A", EnrollmentStatus.PENDING)
    save_roster(db, teacher, klass.seq, JoinMode.APPROVAL, {"A": True})
    assert waiting.status == EnrollmentStatus.PENDING


def test_turned_off_number_is_not_auto_approved(db: Session):
    teacher = make_teacher(db)
    klass = make_class(db, teacher)
    waiting = enroll(db, klass, make_student(db, "A"), "A", EnrollmentStatus.PENDING)
    save_roster(db, teacher, klass.seq, JoinMode.APPROVAL, {"A": False})
    assert waiting.status == EnrollmentStatus.PENDING
