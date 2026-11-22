import pytest
from pydantic import ValidationError

from app.core.enums import PlanCode
from app.core.plans import PLANS
from app.schemas.ai_policy import AiPolicy, default_ai_policy


def test_defaults_match_frontend_default_policy_plus_usage_limit():
    # frontend/src/api/mock/sampleQuestions.ts DEFAULT_POLICY + usage_limit 30 (schema.md D3)
    assert default_ai_policy() == {
        "hint_mode": "EARNED",
        "code_line_limit": 3,
        "hint_penalty": "NONE",
        "variant_enabled": True,
        "variant_graded": False,
        "concept_check_enabled": True,
        "external_signal_enabled": True,
        "report_misconceptions": True,
        "report_dependency": True,
        "prompt_mode": "FORM",
        "custom_prompt": None,
        "usage_limit": 30,
    }


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        AiPolicy.model_validate({"answer_leak": True})


def test_negative_numbers_rejected():
    with pytest.raises(ValidationError):
        AiPolicy(usage_limit=-1)
    with pytest.raises(ValidationError):
        AiPolicy(code_line_limit=-1)


def test_plans_match_schema_d1():
    assert {c: (p.student_limit, p.price) for c, p in PLANS.items()} == {
        PlanCode.SMALL: (50, 90_000),
        PlanCode.MEDIUM: (100, 150_000),
        PlanCode.LARGE: (200, 250_000),
    }
