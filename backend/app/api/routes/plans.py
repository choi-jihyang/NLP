from fastapi import APIRouter

from app.core.plans import PLANS
from app.schemas.classes import PlanOut

router = APIRouter(tags=["plans"])


@router.get("/plans")
def list_plans() -> list[PlanOut]:
    return [PlanOut(code=p.code, name=p.code.value.capitalize(), student_limit=p.student_limit, price=p.price)
            for p in PLANS.values()]
