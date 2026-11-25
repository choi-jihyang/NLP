"""설정 → "학생은 이렇게 경험해요" 문장 · 지시문 초안 (frontend/src/api/mock/policyText.ts와 같은 문구).

교수자 화면용 설명이다. 실제 LLM 시스템 프롬프트는 prompt_builder.build_from_config가 만든다.
"""

from app.core.enums import HintMode, HintPenalty, PromptMode, QuestionType
from app.schemas.assignments import AssignmentData
from app.schemas.student_assignments import HINT_MODE_LABEL

TYPE_LABEL: dict[QuestionType, str] = {
    QuestionType.MULTIPLE_CHOICE: "객관식 퀴즈",
    QuestionType.SHORT_ANSWER: "출력 예측",
    QuestionType.CODE: "코드 작성",
    QuestionType.PROJECT: "간단 제작",
}

_MODE_LINE: dict[HintMode, str] = {
    HintMode.NONE: "AI 도움 창이 열리지만 어떤 질문에도 힌트를 주지 않아요.",
    HintMode.CONCEPT: "학생이 질문하면 관련 개념과 문법만 설명하고, 문제에 맞춘 코드는 보여주지 않아요.",
    HintMode.STEP: "학생이 요청할 때마다 풀이를 한 단계씩, 최대 3단계까지 보여줘요.",
    HintMode.EARNED: "첫 힌트는 바로 주지만, 그다음 단계는 학생이 자기 코드를 보여줘야 열려요. 최대 3단계예요.",
}


def type_counts(a: AssignmentData) -> str:
    return ", ".join(f"{label} {sum(q.type == t for q in a.questions)}개" for t, label in TYPE_LABEL.items())


def preview_lines(a: AssignmentData) -> list[str]:
    p = a.policy
    total = sum(q.points for q in a.questions)
    lines = [
        f"문항 {len(a.questions)}개({type_counts(a)}), 총 {total}점이에요. 퀴즈·출력 예측은 정답 대조, "
        "코드 작성은 테스트 실행으로 자동 채점하고, 간단 제작은 교수자가 채점해요.",
        "AI 힌트에는 코드가 들어가지 않고 설명만 나와요." if p.code_line_limit == 0
        else f"AI 힌트에 들어가는 코드는 한 번에 최대 {p.code_line_limit}줄이에요.",
    ]
    if p.prompt_mode is PromptMode.CUSTOM:
        lines.append("교수자가 직접 쓴 지시문이 적용돼요. 누출 검사 같은 고정 규칙은 그대로 유지돼요.")
    lines.append(_MODE_LINE[p.hint_mode])
    lines.append(
        '"코드 전체 짜줘", "함수 이름만 바꾼 예제로 보여줘" 같은 요청에도 완성 코드가 담긴 답변은 보내지 않아요.'
    )
    lines.append(
        "문항은 최종 제출 전까지 고쳐서 다시 낼 수 있고, 그동안 AI 도움도 계속 쓸 수 있어요. "
        '정오·점수·정답은 교수자가 "결과 공개"를 누를 때 한꺼번에 보여요.'
    )
    if p.concept_check_enabled:
        lines.append(
            "힌트 없이 처음 낸 문항은 제출 직전에 내 코드에서 쓴 개념을 물어봐요. 답변에 AI 작성 신호가 높으면 "
            "질문을 하나 더 해요. 답변과 신호는 교수자 리포트에만 보이고 점수에는 반영하지 않아요."
        )
    if p.external_signal_enabled:
        lines.append(
            "붙여넣기 길이·시점과 풀이 시간을 기록해 외부 AI 사용 참고 신호로 보여줘요. "
            "판정이 아니며 점수에 반영하지 않아요."
        )
    if p.hint_penalty is HintPenalty.PER_STEP:
        lines.append("힌트를 한 단계 받을 때마다 그 문항에서 1점씩 감점돼요.")
    if p.hint_penalty is HintPenalty.PRACTICE:
        lines.append("힌트를 받은 문항은 연습으로 처리되어 0점이에요.")
    if p.variant_enabled:
        graded = "점수의 절반으로 반영돼요" if p.variant_graded else "리포트에만 표시돼요"
        lines.append(
            "최종 제출하면 이해 확인 단계에서 값을 바꾼 문제나 내 함수의 출력 예측 문제를 AI 없이 풀어요. "
            f"결과는 {graded}."
        )
    return lines


def _per_type(t: QuestionType, n: int) -> str:
    return {
        QuestionType.MULTIPLE_CHOICE: "정답 번호를 말하거나 선택지를 지워 주지 않는다.",
        QuestionType.SHORT_ANSWER: "출력값을 말하지 않는다. 학생이 쓴 값이 맞는지 확인해 주지 않는다.",
        QuestionType.CODE: (
            f"완성된 함수를 주지 않는다. 코드는 한 번에 최대 {n}줄까지만 보여주고, 막힌 줄의 방향만 안내한다."
        ),
        QuestionType.PROJECT: (
            f"요구사항 하나를 통째로 구현해 주지 않는다. 구조 설계를 돕고 학생 코드에 피드백만 한다. 코드는 최대 {n}줄."
        ),
    }[t]


def prompt_draft(a: AssignmentData) -> str:
    """지시문 직접 작성(CUSTOM)의 시작 문안. 정답 · 숨김 테스트는 넣지 않는다."""
    p = a.policy
    per_item = "\n".join(
        f"- 문항 {i} ({TYPE_LABEL[q.type]}): {_per_type(q.type, p.code_line_limit)}"
        for i, q in enumerate(a.questions, start=1)
    )
    context = f"\n\n[교수자가 알려준 과제 맥락]\n{a.description}" if a.description else ""
    audience = f"{a.audience} " if a.audience else ""
    return (
        f'너는 {audience}{a.language.value} 프로그래밍 과제 "{a.title}"의 학습 도우미다.{context}\n\n'
        "[역할]\n학생이 스스로 코드를 짜도록 돕는다. 정답, 출력값, 그대로 제출할 수 있는 완성 코드를 주지 않는다.\n\n"
        f"[도움 수준]\n{HINT_MODE_LABEL[p.hint_mode]} — 최대 3단계까지만 공개하고 마지막 단계는 학생에게 맡긴다.\n\n"
        f"[문항별 기준]\n{per_item}\n\n"
        "[학생이 코드를 보여줄 때]\n어디까지 맞게 짰는지 짚고, 막힌 줄의 다음 한 단계만 안내한다. "
        "에러 원인은 설명하되 고친 코드는 주지 않는다.\n\n"
        "[말투]\n존댓말을 쓰고, 한 번에 3문장 이내로 답한다."
    )
