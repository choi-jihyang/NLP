from fastapi import APIRouter

from app.api.deps import DbSession, TeacherUser
from app.schemas.classes import PaymentCreate, PaymentOut
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", status_code=201, response_model_exclude_none=True)  # NEW 응답 모양은 그대로
def create_payment(body: PaymentCreate, teacher: TeacherUser, db: DbSession) -> PaymentOut:
    if body.kind == "EXTEND" and body.class_id is not None:
        payment = payment_service.extend_class(db, teacher, body.class_id, body.plan)
    else:
        payment = payment_service.create_new_payment(db, teacher, body.plan)
    return PaymentOut(
        payment_seq=payment.seq, plan=payment.plan, student_limit=payment.student_limit, amount=payment.amount,
        class_id=payment.class_id, expires_at=payment.period_end if body.kind == "EXTEND" else None,
    )
