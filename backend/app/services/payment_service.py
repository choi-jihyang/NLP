"""결제 목업(NEW만). 실제 결제 대행(PG) 연동 없음 — 항상 성공."""

from sqlalchemy.orm import Session

from app.core.enums import PaymentKind, PlanCode
from app.core.plans import PLANS
from app.models import ClassPayment, User


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
