"""Build a self-contained A100 retry notebook reusing the original private Drive bundle."""

import ast
import json
from pathlib import Path

from make_colab_notebook import cell

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "nlp/colab"
TEMPLATES = MODULES / "templates"


def main():
    sections = [
        (
            "markdown",
            """# StudyChat 실패 건만 재처리 — A100 80GB

기존 성공 결과를 보존하고 기존 full 결과에서 실패한 StudyChat만 재처리합니다.
**세션을 먼저 다시 시작한 뒤** 이 노트북을 위에서부터 실행하세요. 기존 ZIP은 Drive에서 재사용합니다.
기존 4·5·6번 셀을 실행하지 않습니다. 이 노트북에 전용 셀이 들어 있습니다.

기본값: 입력 131,072 / 출력 2,048 / 배치 8 / chunked prefill 16,384.
원본 대화는 자르지 않습니다. 한도를 넘는 입력은 계속 context_overflow로 남습니다.
A100에서는 공식 BF16 Qwen3.5-9B를 사용합니다. 기존 FP8 실행과 모델 정밀도가 달라
별도 폴더와 provenance.json에 기록합니다. 기존 ok 행은 교체하지 않습니다.
실제 A100 모델 로드·처리량은 미검증입니다. 배치 크기는 8배 속도를 보장하지 않습니다.
""",
        )
    ]
    for filename, title in (
        ("01_gpu.py", "1. GPU 확인"),
        ("02_upload.py", "2. 기존 Drive·ZIP 연결"),
        ("03_install.py", "3. 기존 버전 설치 — 재시작 안내 시 1번부터 다시 실행"),
    ):
        sections.extend(
            [("markdown", "## " + title), ("code", (MODULES / "cells" / filename).read_text(encoding="utf-8"))]
        )
    helpers = (MODULES / "retry_workflow.py").read_text(encoding="utf-8")
    prepare = (TEMPLATES / "make_retry_notebook_prepare.py.txt").read_text(encoding="utf-8")
    sections.extend([("markdown", "## 4. 실패 건 선택 — 기존 성공 건은 제외"), ("code", helpers + "\n" + prepare)])
    load = (TEMPLATES / "make_retry_notebook_load.py.txt").read_text(encoding="utf-8")
    # Embed the tested token normalization and annotation validator; no new module upload.
    inference = (MODULES / "inference_vllm.py").read_text(encoding="utf-8")
    annotation_class = inference[inference.index("class Annotator:") :]
    annotation_class = annotation_class.replace("range(2)", "range(3)").replace("if attempt == 0:", "if attempt < 2:")
    annotation_class = annotation_class.replace(
        '". Correct the annotation JSON only; use exact student evidence."',
        '". Return complete JSON including all reasons and an evidence array (empty if appropriate). "\n'
        '                            + "Copy short evidence quotes verbatim, including punctuation and whitespace, "\n'
        '                            + "from a STUDENT turn only. Never paraphrase quotes or cite assistant turns. "\n'
        '                            + "For current attempt=true cite turn=-1 and set cumulative=true. "\n'
        '                            + "For past-only evidence establish the same task; '
        'otherwise use null if uncertain. "\n'
        '                            + "Do not change judgments merely to pass validation. Keep reasons brief."',
    )
    load += (
        "\n"
        + annotation_class
        + """
annotator = Annotator(model, tokenizer, max_input_tokens=MAX_INPUT, max_new_tokens=MAX_OUTPUT)
annotator.batch_size = BATCH_SIZE
retry_config = configuration(manifest, metadata, annotator)
if any(retry_config[k] != base_config[k] for k in ("prompt_version", "prompt_sha256", "source_hashes")):
    raise ValueError("Original prompt/rules/source changed")
retry_config.update(retry_of=stable_hash(base_config), repair_version="exact-evidence-v1-three-attempts",
                    selection_sha256=stable_hash([record_key(s) for s in retry_sources]))
atomic_json(RETRY_ROOT / "current_hardware.json", metadata)
print("배치:", BATCH_SIZE, "입력:", MAX_INPUT, "출력:", MAX_OUTPUT)
"""
    )
    sections.extend([("markdown", "## 5. A100 모델 로드 — 기존 모델 로드 셀 대신 이것만 실행"), ("code", load)])
    execute = (TEMPLATES / "make_retry_notebook_execute.py.txt").read_text(encoding="utf-8")
    full = (TEMPLATES / "make_retry_notebook_full.py.txt").read_text(encoding="utf-8")
    merge = (TEMPLATES / "make_retry_notebook_merge.py.txt").read_text(encoding="utf-8")
    sections.extend(
        [
            ("markdown", "## 6. 먼저 8건으로 엔진·출력 검증"),
            ("code", execute),
            ("markdown", "## 7. 실패 건 전체 재처리·재개"),
            ("code", full),
            ("markdown", "## 8. 기존 성공 보존 후 병합·남은 실패 확인"),
            ("code", merge),
        ]
    )
    cells = []
    for kind, source in sections:
        if kind == "code":
            ast.parse(source)
        cells.append(cell(kind, source))
    notebook = {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"name": "thinkguard_studychat_a100_retry.ipynb", "provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    target = ROOT / "notebooks/thinkguard_studychat_a100_retry.ipynb"
    target.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Generated A100 retry notebook; all code cells parsed; GPU NOT executed")


if __name__ == "__main__":
    main()
