"""학생 입장(수업 코드 + 학번). 다시 입장은 새 토큰 + 다시 승인 대기 (③ 설계 C1 · C2)."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import now_kst
from app.core.enums import EnrollmentStatus, JoinMode, Role
from app.core.errors import AppError, ErrorCode
from app.core.tokens import issue_token
from app.models import ClassMember, ClassRoom, Enrollment, User
from app.services.access import approved_count, find_enrollment


@dataclass(frozen=True)
class JoinResult:
    klass: ClassRoom
    enrollment: Enrollment
    access_token: str


def join(db: Session, invite_code: str, student_no: str, caller: User | None) -> JoinResult:
    """caller: 유효한 토큰의 사용자(없으면 None). student_no는 스키마에서 정리된 값."""
    klass = _open_class(db, invite_code)
    if caller is not None and caller.role != Role.STUDENT:
        raise AppError(ErrorCode.FORBIDDEN, "학생만 수업에 입장할 수 있습니다.")
    now = now_kst()
    existing = db.scalar(
        select(Enrollment).where(Enrollment.class_id == klass.seq, Enrollment.student_no == student_no)
    )
    if existing is not None:
        enrollment = _rejoin(existing, caller)
        account = db.get(User, enrollment.student_id)
        assert account is not None
    else:
        account, enrollment = _first_join(db, klass, student_no, caller, now)
    account.login_at = now
    try:
        db.commit()
    except IntegrityError as exc:  # 같은 학번이 동시에 입장
        db.rollback()
        raise AppError(ErrorCode.CONFLICT) from exc
    return JoinResult(klass, enrollment, issue_token(account, klass.expires_at))


def _open_class(db: Session, invite_code: str) -> ClassRoom:
    klass = db.scalar(select(ClassRoom).where(ClassRoom.invite_code == invite_code.strip().upper()))
    if klass is None:
        raise AppError(ErrorCode.INVITE_CODE_INVALID)
    now = now_kst()
    if now < klass.starts_at:
        raise AppError(ErrorCode.CLASS_NOT_STARTED)
    if now >= klass.expires_at:
        raise AppError(ErrorCode.CLASS_EXPIRED)
    return klass


def _rejoin(enrollment: Enrollment, caller: User | None) -> Enrollment:
    if enrollment.status == EnrollmentStatus.REMOVED:
        raise AppError(ErrorCode.FORBIDDEN, "이 수업에서 내보낸 학번입니다.")
    if enrollment.status == EnrollmentStatus.REJECTED:
        enrollment.status = EnrollmentStatus.PENDING  # 새 요청
        enrollment.decided_at = None
    elif enrollment.status == EnrollmentStatus.APPROVED and (caller is None or caller.seq != enrollment.student_id):
        enrollment.status = EnrollmentStatus.PENDING  # 다시 입장: decided_at을 남겨 구분한다
    return enrollment


def _first_join(
    db: Session, klass: ClassRoom, student_no: str, caller: User | None, now: datetime
) -> tuple[User, Enrollment]:
    if caller is not None and find_enrollment(db, klass.seq, caller.seq) is not None:
        raise AppError(ErrorCode.ALREADY_ENROLLED)
    on_roster = db.scalar(
        select(ClassMember.seq).where(
            ClassMember.class_id == klass.seq, ClassMember.student_no == student_no, ClassMember.is_use.is_(True)
        )
    )
    approve = on_roster is not None or klass.join_mode == JoinMode.OPEN
    if approve and approved_count(db, klass.seq) >= klass.student_limit:
        raise AppError(ErrorCode.CLASS_FULL)
    account = caller if caller is not None else User(role=Role.STUDENT, name=student_no)
    db.add(account)
    db.flush()
    enrollment = Enrollment(
        class_id=klass.seq, student_id=account.seq, student_no=student_no,
        status=EnrollmentStatus.APPROVED if approve else EnrollmentStatus.PENDING,
        decided_at=now if approve else None,
    )
    db.add(enrollment)
    db.flush()
    return account, enrollment
