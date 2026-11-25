"""교수자 간단 제작 채점 (api-contract "리뷰 · 채점")."""

from pydantic import BaseModel, ConfigDict, Field


class GradingItem(BaseModel):
    answer_id: int
    student_name: str
    """학번(student_no)"""
    question_index: int
    """1부터"""
    points: int
    rubric: list[str]
    content: str
    signals: list[str]
    """외부 AI 참고 신호(판정 아님, 점수에 반영하지 않음). 교수자에게만"""
    score: int | None
    feedback: str


class GradeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0)
    feedback: str = Field(default="", max_length=5_000)
