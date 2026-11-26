"""AI 답변 누출 검사 — 학생에게 보내기 전 마지막 필터 (규칙 기반).

백엔드는 LEAK_GUARD_MODULE(기본 thinkguard_nlp.leak:check_leak)로 이 함수를 불러 쓴다.
입출력 형식은 docs/spec/integration-contract.md §4 와 반드시 같아야 한다.
기준 사례: 우회 시도 검증(PR #12 · develop 재검증) — backend/tests/test_leak_guard.py
"""

import re
from typing import Any

from thinkguard_nlp.code_lines import BLANK, DEF, Line, code_units, has_blank, is_answer_expr, string_literals

RECENT_ASSISTANT_TURNS = 4
"""누적 검사에 합치는 최근 AI 답변 수"""
CHUNK_WITH_RETURN = 3
"""빈칸 없는 코드 문장이 이만큼 있고 return이 있으면 완성 코드로 본다"""
CHUNK_ANY = 5
"""빈칸 없는 코드 문장이 이만큼이면 return이 없어도 완성 코드로 본다"""


def check_leak(reply: str, history: list[dict[str, str]]) -> dict[str, Any]:
    """LLM 답변에 정답·완성 코드가 들어 있는지 검사한다.

    Args:
        reply: 학생에게 보내기 전의 LLM 답변 초안
        history: 대화, 오래된 순. 마지막 항목은 이번 학생 메시지.
            {"role": "student" | "assistant", "content": str}
            AI 답변은 누적 검사에, 이번 학생 메시지는 학생이 보낸 빈칸과 비교하는 데 쓴다.

    Returns:
        {"leaked": bool, "reasons": list[str]}
        reasons: complete_function · filled_blank · code_chunk · answer_expression · accumulated
    """
    reasons = _reasons(reply, history)
    for literal in string_literals(reply):
        reasons += _reasons(literal, [])
    reasons = list(dict.fromkeys(reasons))
    return {"leaked": bool(reasons), "reasons": reasons}


def _reasons(text: str, history: list[dict[str, str]]) -> list[str]:
    units = code_units(text)
    reasons = [r for r in _unit_reasons(units) if r]
    if any(is_answer_expr(line) for line in text.splitlines()):
        reasons.append("answer_expression")

    if history and history[-1].get("role") == "student":
        if _fills_student_blank(code_units(history[-1]["content"]), units):
            reasons.append("filled_blank")

    earlier = [t["content"] for t in history if t.get("role") == "assistant"][-RECENT_ASSISTANT_TURNS:]
    if earlier and "complete_function" not in reasons:
        past_units = [u for content in earlier for u in code_units(content)]
        merged = [line for u in [*past_units, *units] if not has_blank(u) for line in u]
        if _is_complete_function(merged) or _filled_blank(past_units, units):
            reasons.append("accumulated")
    return reasons


def _unit_reasons(units: list[list[Line]]) -> list[str | None]:
    filled = [u for u in units if not has_blank(u)]
    stmts = [code for u in filled for kind, code in u if kind == "stmt"]
    has_return = any(code.startswith("return") for code in stmts)
    return [
        "complete_function" if any(_is_complete_function(u) for u in filled) else None,
        "filled_blank" if _filled_blank(units, units) else None,
        "code_chunk" if len(stmts) >= CHUNK_ANY or (len(stmts) >= CHUNK_WITH_RETURN and has_return) else None,
    ]


def _is_complete_function(unit: list[Line]) -> bool:
    """빈칸 없는 def + 본문 (return이 있거나 문장이 CHUNK_WITH_RETURN개 이상)."""
    if not any(kind == "def" for kind, _ in unit):
        return False
    one_liners = [m.group(1) for kind, code in unit if kind == "def" and (m := DEF.match(code)) and m.group(1)]
    body = [code for kind, code in unit if kind == "stmt"] + one_liners
    return any(code.startswith("return") for code in body) or len(body) >= CHUNK_WITH_RETURN


def _filled_blank(blank_sources: list[list[Line]], candidates: list[list[Line]]) -> bool:
    """`deque([____])` 같은 빈칸 줄과 모양이 같고 빈칸만 채워진 줄이 다른 코드 묶음에 있는가."""
    filled_lines = {_squash(code) for u in candidates if not has_blank(u) for _, code in u}
    for unit in blank_sources:
        for kind, code in unit:
            if kind != "blank" or BLANK.fullmatch(code):  # 줄 전체가 빈칸이면 모양으로 비교할 수 없다
                continue
            parts = [re.escape(p) for p in BLANK.split(_squash(code))]
            pattern = re.compile("^" + r"\S.*?".join(parts) + "$")
            if any(pattern.match(line) for line in filled_lines):
                return True
    return False


def _fills_student_blank(student_units: list[list[Line]], units: list[list[Line]]) -> bool:
    """학생이 보낸 빈칸 코드에 답변 코드를 넣으면 완성되는가 (모양이 같은 줄, 또는 줄 전체 빈칸을 다 채움)."""
    if _filled_blank(student_units, units):
        return True
    reply_lines = [line for u in units if not has_blank(u) for line in u]
    reply_stmts = [code for kind, code in reply_lines if kind == "stmt"]
    for unit in student_units:
        blanks = [code for kind, code in unit if kind == "blank"]
        if not blanks or not all(BLANK.fullmatch(b) for b in blanks) or len(reply_stmts) < len(blanks):
            continue
        if _is_complete_function([line for line in unit if line[0] != "blank"] + reply_lines):
            return True
    return False


def _squash(code: str) -> str:
    return re.sub(r"\s+", "", code)
