"""학생 입장(수업 코드 + 학번). 다시 입장은 토큰 대신 대기 티켓 (③ 설계 C1 · C2, schema D21)."""

import hashlib
import secrets
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
    status: EnrollmentStatus  # 응답에 보일 상태. 다시 입장 요청이면 PENDING(참여 자체는 그대로)
    access_token: str | None
    reentry_ticket: str | None = None


@dataclass(frozen=True)
class ClaimResult:
    status: EnrollmentStatus
    access_token: str | None


def ticket_hash(ticket: str) -> str:
    return hashlib.sha256(ticket.encode("utf-8")).hexdigest()


def join(db: Session, invite_code: str, student_no: str, caller: User | None) -> JoinResult:
    """caller: 유효한 토큰의 사용자(없으면 None). student_no는 스키마에서 정리된 값."""
    klass = _open_class(db, invite_code)
    if caller is not None and caller.role != Role.STUDENT:
        raise AppError(ErrorCode.FORBIDDEN, "학생만 수업에 입장할 수 있습니다.")
    now = now_kst()
    existing = db.scalar(
        select(Enrollment).where(Enrollment.class_id == klass.seq, Enrollment.student_no == student_no)
    )
    if existing is not None and existing.status == EnrollmentStatus.REMOVED:
        raise AppError(ErrorCode.FORBIDDEN, "이 수업에서 내보낸 학번입니다.")
    if existing is not None and (caller is None or caller.seq != existing.student_id):
        ticket = _request_reentry(existing, now)
        _commit(db)
        return JoinResult(klass, existing, EnrollmentStatus.PENDING, None, ticket)
    if existing is not None:
        enrollment = _rejoin_own(existing)
        account = caller
    else:
        account, enrollment = _first_join(db, klass, student_no, caller, now)
    assert account is not None
    account.login_at = now
    _commit(db)
    return JoinResult(klass, enrollment, enrollment.status, issue_token(account, klass.expires_at))


def claim_reentry(db: Session, ticket: str) -> ClaimResult:
    """교수자가 수락한 티켓이면 그 계정 토큰을 한 번 주고 티켓을 지운다."""
    enrollment = db.scalar(select(Enrollment).where(Enrollment.reentry_ticket_hash == ticket_hash(ticket)))
    if enrollment is None or enrollment.status == EnrollmentStatus.REMOVED:
        raise AppError(ErrorCode.NOT_FOUND)
    if enrollment.reentry_approved_at is None:
        return ClaimResult(EnrollmentStatus.PENDING, None)
    account = db.get(User, enrollment.student_id)
    klass = db.get(ClassRoom, enrollment.class_id)
    assert account is not None and klass is not None
    clear_reentry(enrollment)
    account.login_at = now_kst()
    db.commit()
    return ClaimResult(enrollment.status, issue_token(account, klass.expires_at))


def clear_reentry(enrollment: Enrollment) -> None:
    enrollment.reentry_ticket_hash = None
    enrollment.reentry_requested_at = None
    enrollment.reentry_approved_at = None


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:  # 같은 학번 · 같은 계정이 동시에 입장
        db.rollback()
        raise AppError(ErrorCode.CONFLICT) from exc


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


def _request_reentry(enrollment: Enrollment, now: datetime) -> str:
    """토큰은 주지 않고 티켓만. 참여 상태 · 자리는 그대로 둔다(리뷰 C1 · C2 · I1)."""
    ticket = secrets.token_urlsafe(32)
    enrollment.reentry_ticket_hash = ticket_hash(ticket)
    enrollment.reentry_requested_at = now
    enrollment.reentry_approved_at = None  # 새로 요청하면 앞선 수락은 무효
    return ticket


def _rejoin_own(enrollment: Enrollment) -> Enrollment:
    if enrollment.status == EnrollmentStatus.REJECTED:
        enrollment.status = EnrollmentStatus.PENDING  # 새 요청
        enrollment.decided_at = None
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
