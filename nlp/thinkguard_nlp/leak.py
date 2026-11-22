"""AI 답변 누출 검사 — 학생에게 보내기 전 마지막 필터 (규칙 기반 1차 구현).

백엔드는 LEAK_GUARD_MODULE(기본 thinkguard_nlp.leak:check_leak)로 이 함수를 불러 쓴다.
입출력 형식은 docs/spec/integration-contract.md §4 와 반드시 같아야 한다.
기준 사례: 우회 시도 검증(PR #12) — backend/tests/test_leak_guard.py
"""

import re
from typing import Any

RECENT_ASSISTANT_TURNS = 4
"""누적 검사에 합치는 최근 AI 답변 수"""
CHUNK_WITH_RETURN = 3
"""빈칸 없는 코드 문장이 이만큼 있고 return이 있으면 완성 코드로 본다"""
CHUNK_ANY = 5
"""빈칸 없는 코드 문장이 이만큼이면 return이 없어도 완성 코드로 본다"""

_FENCE = re.compile(r"```[^\n]*\n(.*?)(?:```|\Z)", re.S)
_INLINE = re.compile(r"`([^`\n]+)`")
_BLANK = re.compile(r"_{3,}")
_HANGUL = re.compile(r"[가-힣]")
_STRING = re.compile(r"'[^']*'|\"[^\"]*\"")
_LIST_MARK = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+")
_DEF = re.compile(r"^def\s+\w+\s*\(.*\)\s*(?:->.*)?:\s*(.*)$")
_KEYWORD = re.compile(
    r"^(?:return|for|while|if|elif|else|try|except|finally|with|class|break|continue|pass|raise|yield)\b"
)
_IMPORT = re.compile(r"^(?:import\s+\w|from\s+[\w.]+\s+import\s+\w)")
_ASSIGN = re.compile(r"^[A-Za-z_][\w.\[\]'\", ]*\s*(?:[-+*/%]|//)?=(?!=)\s*\S")
_CALL = re.compile(r"^[A-Za-z_][\w.]*\(.*\)$")
_ANSWER_EXPR = (
    re.compile(r"\b(?:sum|max|min|sorted|len|any|all)\s*\(.*\bfor\b.+\bin\b"),  # sum(x for x in …)
    re.compile(r"[\[(].*\bfor\b.+\bin\b.+\bif\b"),  # [x for x in … if …]
    re.compile(r"\b(?:sorted|max|min)\s*\(.*\)\s*\[-?\d+\]"),  # sorted(set(x))[1]
)

Line = tuple[str, str]
"""(종류, 정리된 코드) — 종류: def · stmt · import · blank"""


def check_leak(reply: str, history: list[dict[str, str]]) -> dict[str, Any]:
    """LLM 답변에 정답·완성 코드가 들어 있는지 검사한다.

    Args:
        reply: 학생에게 보내기 전의 LLM 답변 초안
        history: 이전 대화, 오래된 순. {"role": "student" | "assistant", "content": str}
            AI 답변(role="assistant")만 누적 검사에 쓴다.

    Returns:
        {"leaked": bool, "reasons": list[str]}
        reasons: complete_function · filled_blank · code_chunk · answer_expression · accumulated
    """
    units = _code_units(reply)
    reasons = [r for r in _unit_reasons(units) if r]
    if any(_is_answer_expr(code) for unit in units for _, code in unit):
        reasons.append("answer_expression")

    earlier = [t["content"] for t in history if t.get("role") == "assistant"][-RECENT_ASSISTANT_TURNS:]
    if earlier and "complete_function" not in reasons:
        past_units = [u for text in earlier for u in _code_units(text)]
        merged = [line for u in [*past_units, *units] if not _has_blank(u) for line in u]
        if _is_complete_function(merged) or _filled_blank(past_units, units):
            reasons.append("accumulated")
    return {"leaked": bool(reasons), "reasons": list(dict.fromkeys(reasons))}


# ---- 판정 규칙 --------------------------------------------------------------


def _unit_reasons(units: list[list[Line]]) -> list[str | None]:
    filled = [u for u in units if not _has_blank(u)]
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
    one_liners = [m.group(1) for kind, code in unit if kind == "def" and (m := _DEF.match(code)) and m.group(1)]
    body = [code for kind, code in unit if kind == "stmt"] + one_liners
    return any(code.startswith("return") for code in body) or len(body) >= CHUNK_WITH_RETURN


def _filled_blank(blank_sources: list[list[Line]], candidates: list[list[Line]]) -> bool:
    """빈칸(____) 줄과 같은 모양인데 빈칸이 채워진 줄이 다른 코드 묶음에 있는가."""
    filled_lines = {_squash(code) for u in candidates if not _has_blank(u) for _, code in u}
    for unit in blank_sources:
        for kind, code in unit:
            if kind != "blank":
                continue
            parts = [re.escape(p) for p in _BLANK.split(_squash(code))]
            pattern = re.compile("^" + r"\S.*?".join(parts) + "$")
            if any(pattern.match(line) for line in filled_lines):
                return True
    return False


def _is_answer_expr(code: str) -> bool:
    return not _BLANK.search(code) and any(p.search(code) for p in _ANSWER_EXPR)


def _has_blank(unit: list[Line]) -> bool:
    return any(kind == "blank" for kind, _ in unit)


def _squash(code: str) -> str:
    return re.sub(r"\s+", "", code)


# ---- 답변에서 코드 줄 뽑기 ----------------------------------------------------


def _code_units(text: str) -> list[list[Line]]:
    """코드블록 하나, 또는 코드블록 밖에서 이어진 코드 줄들이 한 묶음."""
    units = [_parse_lines(block.splitlines()) for block in _FENCE.findall(text)]
    current: list[Line] = []
    for raw in _FENCE.sub("\n", text).splitlines():
        spans = _INLINE.findall(raw)
        snippets = spans if spans else [raw]
        lines = [line for s in snippets if (line := _classify(s))]
        if lines:
            current += [line for line in lines if line[0] != "comment"]
        elif raw.strip():
            units.append(current)
            current = []
    units.append(current)
    return [u for u in units if u]


def _parse_lines(lines: list[str]) -> list[Line]:
    return [line for raw in lines if (line := _classify(raw)) and line[0] != "comment"]


def _classify(raw: str) -> Line | None:
    """코드 한 줄이면 (종류, 코드), 아니면 None. 한글이 섞인 줄은 설명문으로 본다(주석·문자열 제외)."""
    code = _LIST_MARK.sub("", raw).strip()
    if not code:
        return None
    if code.startswith("#"):
        return ("comment", code)
    bare = _STRING.sub("''", code).split("#", 1)[0].strip()
    if not bare or _HANGUL.search(bare):
        return None
    if _BLANK.search(bare):
        return ("blank", bare)
    if _DEF.match(bare):
        return ("def", bare)
    if _IMPORT.match(bare):
        return ("import", bare)
    is_keyword = _KEYWORD.match(bare) and (len(bare.split()) > 1 or bare.endswith(":"))
    if is_keyword or _ASSIGN.match(bare) or _CALL.match(bare) or _is_answer_expr(bare):
        return ("stmt", bare)
    return None
