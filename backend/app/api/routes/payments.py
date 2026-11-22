from fastapi import APIRouter

from app.api.deps import DbSession, TeacherUser
from app.schemas.classes import PaymentCreate, PaymentOut
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", status_code=201)
def create_payment(body: PaymentCreate, teacher: TeacherUser, db: DbSession) -> PaymentOut:
    payment = payment_service.create_new_payment(db, teacher, body.plan)
    return PaymentOut(
        payment_seq=payment.seq, plan=payment.plan, student_limit=payment.student_limit, amount=payment.amount
    )
