"""시연용 시드 데이터. 실행: cd backend && .venv/bin/python -m app.seed

비밀번호는 시연용 테스트 값이다. 실제 비밀번호를 쓰지 않는다.
과제·문항 시드는 과제 테이블이 생기는 ④ 과제 API에서 추가한다.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import add_years, now_kst, start_of_day_kst
from app.core.enums import EnrollmentStatus, PaymentKind, PlanCode, Role
from app.core.plans import PLANS
from app.core.security import hash_password
from app.models import ClassMember, ClassPayment, ClassRoom, Enrollment, User

SEED_TEACHER_EMAIL = "teacher@thinkguard.test"
SEED_TEACHER_PASSWORD = "thinkguard-demo"
SEED_INVITE_CODE = "TG-4821"
SEED_STUDENT_NOS = ("20260001", "20260002", "20260003")
SEED_ROSTER_ONLY_NO = "20260004"  # 명단에는 있지만 아직 입장하지 않은 학번


class SeedAlreadyLoadedError(RuntimeError):
    pass


def seed(db: Session, today: date | None = None) -> ClassRoom:
    if db.scalar(select(User).where(User.email == SEED_TEACHER_EMAIL)) is not None:
        raise SeedAlreadyLoadedError("시드 데이터가 이미 있습니다. thinkguard.db를 지우고 다시 실행하세요.")

    now = now_kst()
    starts_at = start_of_day_kst(today or now.date())
    expires_at = add_years(starts_at, 1)
    plan = PLANS[PlanCode.SMALL]

    teacher = User(
        role=Role.TEACHER, email=SEED_TEACHER_EMAIL,
        password_hash=hash_password(SEED_TEACHER_PASSWORD), name="김교수",
    )
    db.add(teacher)
    db.flush()

    klass = ClassRoom(
        teacher_id=teacher.seq, name="프로그래밍 기초 1분반", invite_code=SEED_INVITE_CODE,
        plan=plan.code, student_limit=plan.student_limit, starts_at=starts_at, expires_at=expires_at,
    )
    db.add(klass)
    db.flush()

    db.add(ClassPayment(
        teacher_id=teacher.seq, class_id=klass.seq, plan=plan.code, student_limit=plan.student_limit,
        kind=PaymentKind.NEW, amount=plan.price, period_start=starts_at, period_end=expires_at,
    ))
    for no in (*SEED_STUDENT_NOS, SEED_ROSTER_ONLY_NO):
        db.add(ClassMember(class_id=klass.seq, student_no=no))
    for no in SEED_STUDENT_NOS:
        student = User(role=Role.STUDENT, name=no)
        db.add(student)
        db.flush()
        db.add(Enrollment(
            class_id=klass.seq, student_id=student.seq, student_no=no,
            status=EnrollmentStatus.APPROVED, decided_at=now,
        ))
    db.commit()
    return klass


def main() -> None:
    from app.db.init_db import init_db
    from app.db.session import SessionLocal, engine

    init_db(engine)
    with SessionLocal() as db:
        try:
            klass = seed(db)
        except SeedAlreadyLoadedError as e:
            print(e)
            raise SystemExit(1) from e
    students = ", ".join(SEED_STUDENT_NOS)
    print(f"시드 완료: 교수자 {SEED_TEACHER_EMAIL} / 수업 코드 {klass.invite_code} / 학번 {students}")


if __name__ == "__main__":
    main()
