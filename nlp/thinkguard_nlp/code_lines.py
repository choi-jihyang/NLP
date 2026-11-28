"""답변·학생 메시지에서 코드 줄을 뽑아 묶음으로 나눈다 (누출 검사 leak.py가 쓴다)."""

import ast
import re

BLANK = re.compile(r"_{3,}")

_FENCE = re.compile(r"```[^\n]*\n(.*?)(?:```|\Z)", re.S)
_INLINE = re.compile(r"`([^`\n]+)`")
_HANGUL = re.compile(r"[가-힣]")
_STRING = re.compile(r"'[^']*'|\"[^\"]*\"")
_LITERAL = re.compile(r"'((?:\\.|[^'\\\n])+)'|\"((?:\\.|[^\"\\\n])+)\"")
_LIST_MARK = re.compile(r"^\s*(?:\d+[.)]|[-*•>])\s+")  # 목록 · 인용(> ) 표시
DEF = re.compile(r"^def\s+\w+\s*\(.*\)\s*(?:->.*)?:\s*(.*)$")
_KEYWORD = re.compile(
    r"^(?:return|for|while|if|elif|else|try|except|finally|with|class|break|continue|pass|raise|yield)\b"
)
_IMPORT = re.compile(r"^(?:import\s+\w|from\s+[\w.]+\s+import\s+\w)")
_ASSIGN = re.compile(r"^[^\W\d][\w.\[\]'\", ]*\s*(?:[-+*/%]|//)?=(?!=)\s*\S")
_CALL = re.compile(r"^[^\W\d][\w.]*\(.*\)$")
_DECOY = re.compile(r"^([^\W\d]\w*)\s*=\s*_{3,}$")
ANSWER_EXPR = (
    re.compile(r"\b(?:sum|max|min|sorted|len|any|all)\s*\(.*\bfor\b.+\bin\b"),  # sum(x for x in …)
    re.compile(r"[\[(].*\bfor\b.+\bin\b.+\bif\b"),  # [x for x in … if …]
    re.compile(r"\b(?:sorted|max|min)\s*\(.*\)\s*\[-?\d+\]"),  # sorted(set(x))[1]
)

Line = tuple[str, str]
"""(종류, 정리된 코드) — 종류: def · stmt · import · blank · expr(n % 2 == 0 같은 식)"""


def code_units(text: str) -> list[list[Line]]:
    """코드블록 하나, 또는 코드블록 밖에서 이어진 코드 줄들이 한 묶음."""
    units = [_parse_lines(block.splitlines()) for block in _FENCE.findall(text)]
    current: list[Line] = []
    for raw in _FENCE.sub("\n", text).splitlines():
        spans = _INLINE.findall(raw)
        lines = [line for s in (spans or _table_cells(raw) or [raw]) if (line := classify(s))]
        if lines:
            current += [line for line in lines if line[0] != "comment"]
        elif raw.strip():
            units.append(current)
            current = []
    units.append(current)
    return [_drop_decoy_blanks(u) for u in units if u]


def _table_cells(raw: str) -> list[str]:
    """마크다운 표 행(| 1 | def f(x): |)이면 칸마다 코드 후보로 본다."""
    row = raw.strip()
    return row.strip("|").split("|") if row.startswith("|") and row.count("|") >= 2 else []


def string_literals(text: str) -> list[str]:
    """따옴표 안 내용 (print("def …") 처럼 코드를 문자열에 숨긴 경우를 다시 검사하려고)."""
    found = [a or b for a, b in _LITERAL.findall(text)]
    return [s.replace("\\n", "\n").replace("\\t", "    ") for s in found if len(s) >= 8]


def is_answer_expr(code: str) -> bool:
    return not BLANK.search(code) and any(p.search(code) for p in ANSWER_EXPR)


def has_blank(unit: list[Line]) -> bool:
    return any(kind == "blank" for kind, _ in unit)


def classify(raw: str) -> Line | None:
    """코드 한 줄이면 (종류, 코드), 아니면 None.

    한글이 섞인 줄은 파이썬으로 읽힐 때만 코드로 본다(한글 변수 이름 허용, 한국어 설명문 제외).
    """
    code = _LIST_MARK.sub("", raw).strip()
    if not code:
        return None
    if code.startswith("#"):
        return ("comment", code)
    bare = _STRING.sub("''", code).split("#", 1)[0].strip()
    if not bare or (_HANGUL.search(bare) and not _parses(bare)):
        return None
    if BLANK.search(bare):
        return ("blank", bare)
    if DEF.match(bare):
        return ("def", bare)
    if _IMPORT.match(bare):
        return ("import", bare)
    is_keyword = _KEYWORD.match(bare) and (len(bare.split()) > 1 or bare.endswith(":"))
    if is_keyword or _ASSIGN.match(bare) or _CALL.match(bare) or is_answer_expr(bare):
        return ("stmt", bare)
    if _parses(bare):
        return ("expr", bare)
    return None


def _parse_lines(lines: list[str]) -> list[Line]:
    return [line for raw in lines if (line := classify(raw)) and line[0] != "comment"]


def _parses(code: str) -> bool:
    """한 줄을 파이썬 문장으로 읽을 수 있는가. 이름·값 하나뿐인 줄(한국어 낱말)은 제외."""
    src = BLANK.sub("_b_", code)
    if re.match(r"(?:elif|else)\b", src):
        src = "if 1:\n pass\n" + src
    elif re.match(r"(?:except|finally)\b", src):
        src = "try:\n pass\n" + src
    if src.endswith(":"):
        src += "\n pass"
    try:
        last = ast.parse(src).body[-1]
    except SyntaxError:
        return False
    return not (isinstance(last, ast.Expr) and isinstance(last.value, ast.Name | ast.Constant))


def _drop_decoy_blanks(unit: list[Line]) -> list[Line]:
    """`unused = ____` 처럼 어디에서도 쓰지 않는 이름에 빈칸을 넣은 줄은 빈칸으로 치지 않는다."""
    kept = []
    for i, (kind, code) in enumerate(unit):
        m = _DECOY.match(code) if kind == "blank" else None
        others = (c for j, (_, c) in enumerate(unit) if j != i)
        if m and not any(re.search(rf"\b{re.escape(m.group(1))}\b", c) for c in others):
            continue
        kept.append((kind, code))
    return kept
