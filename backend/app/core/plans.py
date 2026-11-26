"""요금제 (schema.md D1). 테이블 없이 코드 상수로 둔다. 기능은 같고 학생 수 상한만 다르다."""

from dataclasses import dataclass

from app.core.enums import PlanCode


@dataclass(frozen=True)
class Plan:
    code: PlanCode
    student_limit: int
    price: int  # 원, 클래스 하나 · 1년


PLANS: dict[PlanCode, Plan] = {
    PlanCode.SMALL: Plan(PlanCode.SMALL, 50, 90_000),
    PlanCode.MEDIUM: Plan(PlanCode.MEDIUM, 100, 150_000),
    PlanCode.LARGE: Plan(PlanCode.LARGE, 200, 250_000),
}
