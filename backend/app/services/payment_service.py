"""결제 목업(NEW · EXTEND). 실제 결제 대행(PG) 연동 없음 — 항상 성공."""

from sqlalchemy.orm import Session

from app.core.clock import add_years
from app.core.enums import PaymentKind, PlanCode
from app.core.errors import AppError, ErrorCode
from app.core.plans import PLANS
from app.models import ClassPayment, User
from app.services.access import approved_count, own_class


def create_new_payment(db: Session, teacher: User, plan: PlanCode) -> ClassPayment:
    """아직 클래스에 연결되지 않은 이용권. 금액·상한은 요금제 표에서만 가져온다."""
    info = PLANS[plan]
    payment = ClassPayment(
        teacher_id=teacher.seq, class_id=None, plan=info.code, student_limit=info.student_limit,
        kind=PaymentKind.NEW, amount=info.price,
    )
    db.add(payment)
    db.commit()
    return payment


def extend_class(db: Session, teacher: User, class_id: int, plan: PlanCode) -> ClassPayment:
    """내 클래스 기간을 1년 늘린다. 요금제를 바꿀 수 있지만 지금 학생 수보다 작은 요금제는 안 된다."""
    klass = own_class(db, teacher, class_id)
    info = PLANS[plan]
    if info.student_limit < approved_count(db, klass.seq):
        raise AppError(ErrorCode.CONFLICT, "지금 학생 수보다 작은 요금제로는 연장할 수 없습니다.")
    start = klass.expires_at
    klass.expires_at = add_years(start, 1)
    klass.plan, klass.student_limit = info.code, info.student_limit
    payment = ClassPayment(
        teacher_id=teacher.seq, class_id=klass.seq, plan=info.code, student_limit=info.student_limit,
        kind=PaymentKind.EXTEND, amount=info.price, period_start=start, period_end=klass.expires_at,
    )
    db.add(payment)
    db.commit()
    return payment
