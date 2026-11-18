"""Apply the teammate's length scheduling/benchmark approach to owner's 32K-only retry."""

import ast
import json
from pathlib import Path

from make_colab_notebook import cell

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "nlp/colab"
TEMPLATES = MODULES / "templates"


def main():
    base = json.loads((ROOT / "notebooks/thinkguard_studychat_a100_retry.ipynb").read_text(encoding="utf-8"))
    cells = base["cells"][:11]  # Intro + original setup cells 1 through 5.
    cells[0] = cell(
        "markdown",
        """# StudyChat A100 재처리 — 32K 이하, 배치 자동 비교

세션을 다시 시작하고 위에서부터 실행합니다. 기존 성공과 이전 A100 재처리 성공을 보존합니다.
입력 32,000토큰 초과는 추론하지 않습니다. 전체 대화를 자르거나 요약하지 않습니다.
팀원 방식: 길이 캐시, 길이/대화별 정렬, 동일 표본으로 배치 2·4·8 비교, 표본 성공 재사용.
출력은 2,048토큰을 유지하고 최대 시도는 3회에서 2회로 줄였습니다.
모델은 기존 A100 실행과 같은 공식 BF16 리비전을 재사용합니다.
실제 GPU 속도는 미검증입니다. 메모리/CUDA 오류가 나면 비교를 중단하고 원인 로그를 확인합니다.
""",
    )
    prepare = "".join(cells[8]["source"])
    prepare = prepare.replace(
        'RETRY_ROOT = PROJECT_DIR / "qwen35_9b_a100_bf16_retry_v1"',
        (
            'PREVIOUS_ROOT = PROJECT_DIR / "qwen35_9b_a100_bf16_retry_v1"\nRETRY_ROOT = P'
            'ROJECT_DIR / "qwen35_9b_a100_32k_optimized_v1"'
        ),
    )
    prepare = prepare.replace("MAX_INPUT = 131072", "MAX_INPUT = 32000")
    extra = (TEMPLATES / "make_optimized_retry_notebook_extra.py.txt").read_text(encoding="utf-8")
    # The setup installer uses 'installed', just as the teammate's notebook does.
    cells[8] = cell("code", (MODULES / "optimized_retry.py").read_text(encoding="utf-8") + "\n" + prepare + extra)
    load = "".join(cells[10]["source"])
    # Keep strengthened evidence repair instructions, but limit expensive repeat calls.
    load = load.replace("range(3)", "range(2)").replace("if attempt < 2:", "if attempt < 1:")
    load = load.replace(
        'repair_version="exact-evidence-v1-three-attempts"', 'repair_version="exact-evidence-v2-two-attempts"'
    )
    load = load.replace(
        "enable_chunked_prefill=True, enforce_eager=True, seed=0)",
        "enable_chunked_prefill=True, enable_prefix_caching=True, enforce_eager=True, seed=0)",
    )
    load += """
for _, config in attempts:
    # Cross-profile reuse is allowed only for the same BF16 weights, prompt and versions.
    for key in ("model_id", "revision", "quantization", "versions"):
        if config["model"].get(key) != metadata.get(key):
            raise ValueError("Previous successful attempt uses a different model/environment: " + key)
"""
    cells[10] = cell("code", load)
    benchmark = (TEMPLATES / "make_optimized_retry_notebook_benchmark.py.txt").read_text(encoding="utf-8")
    full = (TEMPLATES / "make_optimized_retry_notebook_full.py.txt").read_text(encoding="utf-8")
    merge = (TEMPLATES / "make_optimized_retry_notebook_merge.py.txt").read_text(encoding="utf-8")
    cells += [
        cell("markdown", "## 6. 길이 캐시·32K 초과 제외·배치 2/4/8 비교"),
        cell("code", benchmark),
        cell("markdown", "## 7. 선택 배치로 실행·재개"),
        cell("code", full),
        cell("markdown", "## 8. 성공 보존·누락/중복/실패 검사 및 병합"),
        cell("code", merge),
    ]
    for c in cells:
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]))
    base["cells"] = cells
    base["metadata"]["colab"]["name"] = "thinkguard_studychat_a100_32k_optimized.ipynb"
    target = ROOT / "notebooks/thinkguard_studychat_a100_32k_optimized.ipynb"
    target.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Generated optimized notebook; all cells parsed; GPU not tested")


if __name__ == "__main__":
    main()
