"""클래스 개설(결제 → 개설, 한 트랜잭션) · 목록 · 상세 · AI 기본값."""

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.clock import add_years, now_kst, start_of_day_kst
from app.core.enums import PaymentKind, PromptMode
from app.core.errors import AppError, ErrorCode
from app.models import ClassPayment, ClassRoom, User
from app.schemas.ai_policy import AiPolicy, default_ai_policy
from app.services.access import approved_count, own_class

MAX_CODE_TRIES = 10
_UNUSABLE_PAYMENT = "사용할 수 없는 결제입니다."


@dataclass(frozen=True)
class ClassView:
    klass: ClassRoom
    student_count: int


def random_invite_code() -> str:
    return f"TG-{1000 + secrets.randbelow(9000)}"


def _unused_code(db: Session, make_code: Callable[[], str]) -> str:
    for _ in range(MAX_CODE_TRIES):
        code = make_code()
        if db.scalar(select(ClassRoom.seq).where(ClassRoom.invite_code == code)) is None:
            return code
    raise AppError(ErrorCode.INTERNAL_ERROR, "수업 코드를 만들지 못했습니다. 다시 시도해 주세요.")


def _usable_payment(db: Session, teacher: User, payment_seq: int) -> ClassPayment:
    payment = db.get(ClassPayment, payment_seq)
    if payment is None:
        raise AppError(ErrorCode.NOT_FOUND)
    if payment.teacher_id != teacher.seq or payment.kind != PaymentKind.NEW or payment.class_id is not None:
        raise AppError(ErrorCode.CONFLICT, _UNUSABLE_PAYMENT)
    return payment


def create_class(
    db: Session,
    teacher: User,
    name: str,
    starts_on: date,
    payment_seq: int,
    *,
    today: date | None = None,
    make_code: Callable[[], str] = random_invite_code,
) -> ClassRoom:
    if starts_on < (today or now_kst().date()):
        raise AppError(ErrorCode.VALIDATION_FAILED, "시작 날짜는 오늘 이후여야 합니다.")
    payment = _usable_payment(db, teacher, payment_seq)
    starts_at = start_of_day_kst(starts_on)
    expires_at = add_years(starts_at, 1)
    klass = ClassRoom(
        teacher_id=teacher.seq, name=name, invite_code=_unused_code(db, make_code), plan=payment.plan,
        student_limit=payment.student_limit, starts_at=starts_at, expires_at=expires_at,
        ai_defaults=default_ai_policy(),
    )
    db.add(klass)
    db.flush()
    claimed = db.execute(
        update(ClassPayment)
        .where(ClassPayment.seq == payment.seq, ClassPayment.class_id.is_(None))
        .values(class_id=klass.seq, period_start=starts_at, period_end=expires_at)
    )
    if claimed.rowcount != 1:  # 같은 결제로 동시에 개설
        db.rollback()
        raise AppError(ErrorCode.CONFLICT, _UNUSABLE_PAYMENT)
    db.commit()
    return klass


def list_classes(db: Session, teacher: User) -> list[ClassView]:
    classes = db.scalars(select(ClassRoom).where(ClassRoom.teacher_id == teacher.seq).order_by(ClassRoom.seq.desc()))
    return [ClassView(k, approved_count(db, k.seq)) for k in classes]


def get_class_view(db: Session, teacher: User, class_id: int) -> ClassView:
    klass = own_class(db, teacher, class_id)
    return ClassView(klass, approved_count(db, klass.seq))


def get_ai_defaults(db: Session, teacher: User, class_id: int) -> AiPolicy:
    return AiPolicy.model_validate(own_class(db, teacher, class_id).ai_defaults)


def save_ai_defaults(db: Session, teacher: User, class_id: int, policy: AiPolicy) -> AiPolicy:
    """클래스 기본값은 양식(FORM)만. 지시문 직접 작성은 과제마다 한다."""
    klass = own_class(db, teacher, class_id)
    forced = policy.model_copy(update={"prompt_mode": PromptMode.FORM, "custom_prompt": None})
    klass.ai_defaults = forced.model_dump(mode="json")  # 새 dict 대입(JSON 안쪽 변경은 저장 안 됨)
    db.commit()
    return forced
