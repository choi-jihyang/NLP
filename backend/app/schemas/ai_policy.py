"""AI 정책 JSON (schema.md AiPolicy). classes.ai_defaults · assignments.policy 컬럼의 모양."""

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import HintMode, HintPenalty, PromptMode


class AiPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hint_mode: HintMode = HintMode.EARNED
    code_line_limit: int = Field(default=3, ge=0)
    hint_penalty: HintPenalty = HintPenalty.NONE
    variant_enabled: bool = True
    variant_graded: bool = False
    concept_check_enabled: bool = True
    external_signal_enabled: bool = True
    report_misconceptions: bool = True
    report_dependency: bool = True
    prompt_mode: PromptMode = PromptMode.FORM
    custom_prompt: str | None = None
    usage_limit: int = Field(default=30, ge=0)


def default_ai_policy() -> dict[str, object]:
    """JSON 컬럼 기본값. Enum은 문자열로."""
    return AiPolicy().model_dump(mode="json")
