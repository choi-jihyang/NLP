import re
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.core.enums import JoinMode, PaymentKind, PlanCode, PromptMode
from app.core.errors import AppError, ErrorCode
from app.models import ClassPayment
from app.schemas.ai_policy import AiPolicy, default_ai_policy
from app.services.class_service import (
    create_class,
    get_ai_defaults,
    get_class_view,
    list_classes,
    random_invite_code,
    save_ai_defaults,
)
from app.services.payment_service import create_new_payment
from tests.factories import enroll, make_class, make_student, make_teacher

TODAY = date(2026, 11, 22)


def _create(db: Session, teacher, payment_seq: int, starts_on: date = date(2027, 3, 2), **kw):  # noqa: ANN001
    return create_class(db, teacher, "1분반", starts_on, payment_seq, today=TODAY, **kw)


def _error(fn, *args, **kw) -> ErrorCode:  # noqa: ANN001
    with pytest.raises(AppError) as info:
        fn(*args, **kw)
    return info.value.code


def test_new_payment_uses_plan_table(db: Session):
    payment = create_new_payment(db, make_teacher(db), PlanCode.MEDIUM)
    assert (payment.plan, payment.student_limit, payment.amount, payment.kind) == (
        PlanCode.MEDIUM, 100, 150_000, PaymentKind.NEW,
    )
    assert payment.class_id is None and payment.period_start is None and payment.period_end is None


def test_create_class_copies_payment_and_links_it(db: Session):
    teacher = make_teacher(db)
    payment = create_new_payment(db, teacher, PlanCode.MEDIUM)
    klass = _create(db, teacher, payment.seq)
    assert (klass.plan, klass.student_limit, klass.join_mode) == (PlanCode.MEDIUM, 100, JoinMode.APPROVAL)
    assert klass.starts_at.isoformat() == "2027-03-02T00:00:00+09:00"
    assert klass.expires_at.isoformat() == "2028-03-02T00:00:00+09:00"
    assert re.fullmatch(r"TG-\d{4}", klass.invite_code)
    assert klass.ai_defaults == default_ai_policy()
    db.refresh(payment)
    linked = (payment.class_id, payment.period_start, payment.period_end)
    assert linked == (klass.seq, klass.starts_at, klass.expires_at)


def test_start_today_ok_yesterday_rejected(db: Session):
    teacher = make_teacher(db)
    ok = create_new_payment(db, teacher, PlanCode.SMALL)
    assert _create(db, teacher, ok.seq, starts_on=TODAY).starts_at.date() == TODAY
    late = create_new_payment(db, teacher, PlanCode.SMALL)
    assert _error(_create, db, teacher, late.seq, starts_on=date(2026, 11, 21)) == ErrorCode.VALIDATION_FAILED


def test_payment_must_be_mine_unused_and_new(db: Session):
    teacher, other = make_teacher(db, "a@x.test"), make_teacher(db, "b@x.test")
    others = create_new_payment(db, other, PlanCode.SMALL)
    assert _error(_create, db, teacher, others.seq) == ErrorCode.CONFLICT
    mine = create_new_payment(db, teacher, PlanCode.SMALL)
    _create(db, teacher, mine.seq)
    assert _error(_create, db, teacher, mine.seq) == ErrorCode.CONFLICT  # 이미 쓴 결제
    extend = ClassPayment(
        teacher_id=teacher.seq, plan=PlanCode.SMALL, student_limit=50, kind=PaymentKind.EXTEND, amount=1
    )
    db.add(extend)
    db.commit()
    assert _error(_create, db, teacher, extend.seq) == ErrorCode.CONFLICT
    assert _error(_create, db, teacher, 999) == ErrorCode.NOT_FOUND


def test_invite_code_collision_retries(db: Session):
    teacher = make_teacher(db)
    make_class(db, teacher, code="TG-1111")
    codes = iter(["TG-1111", "TG-2222"])
    payment = create_new_payment(db, teacher, PlanCode.SMALL)
    assert _create(db, teacher, payment.seq, make_code=lambda: next(codes)).invite_code == "TG-2222"


def test_invite_code_gives_up_after_ten_tries(db: Session):
    teacher = make_teacher(db)
    make_class(db, teacher, code="TG-1111")
    payment = create_new_payment(db, teacher, PlanCode.SMALL)
    assert _error(_create, db, teacher, payment.seq, make_code=lambda: "TG-1111") == ErrorCode.INTERNAL_ERROR
    db.refresh(payment)
    assert payment.class_id is None  # 결제는 그대로 남아 다시 쓸 수 있다


def test_random_invite_code_format():
    assert all(re.fullmatch(r"TG-[1-9]\d{3}", random_invite_code()) for _ in range(50))


def test_list_and_get_count_approved_students_only(db: Session):
    teacher, other = make_teacher(db, "a@x.test"), make_teacher(db, "b@x.test")
    mine = make_class(db, teacher, code="TG-1001")
    make_class(db, other, code="TG-1002")
    enroll(db, mine, make_student(db, "a"), "a")
    from app.core.enums import EnrollmentStatus

    enroll(db, mine, make_student(db, "b"), "b", EnrollmentStatus.PENDING)
    views = list_classes(db, teacher)
    assert [(v.klass.seq, v.student_count) for v in views] == [(mine.seq, 1)]
    assert get_class_view(db, teacher, mine.seq).student_count == 1


def test_ai_defaults_saved_as_form(db: Session):
    teacher = make_teacher(db)
    klass = make_class(db, teacher)
    saved = save_ai_defaults(
        db, teacher, klass.seq, AiPolicy(prompt_mode=PromptMode.CUSTOM, custom_prompt="정답 줘", usage_limit=10)
    )
    assert (saved.prompt_mode, saved.custom_prompt, saved.usage_limit) == (PromptMode.FORM, None, 10)
    db.expire_all()
    assert get_ai_defaults(db, teacher, klass.seq).usage_limit == 10


def test_ai_defaults_other_teacher_forbidden(db: Session):
    owner, other = make_teacher(db, "a@x.test"), make_teacher(db, "b@x.test")
    klass = make_class(db, owner)
    assert _error(get_ai_defaults, db, other, klass.seq) == ErrorCode.FORBIDDEN
