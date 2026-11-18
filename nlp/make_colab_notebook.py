"""검토 가능한 셀 원본으로부터 데이터 없는 Colab 노트북을 생성한다."""

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELLS = ROOT / "nlp/colab/cells"
OUT = ROOT / "notebooks/thinkguard_qwen35_9b_vllm_labeling.ipynb"
SECTIONS = [
    ("01_gpu.py", "1. GPU 확인", "Colab에서 런타임 유형을 GPU로 설정하세요. GPU가 없으면 즉시 멈춥니다."),
    (
        "02_upload.py",
        "2. Drive 연결·입력 업로드",
        "함께 제공한 ZIP을 한 번만 업로드합니다. 다음 세션은 Drive에서 읽습니다.",
    ),
    ("03_install.py", "3. 추론 패키지 설치", "첫 설치 버전을 Drive에 기록하고 재접속 시 같은 버전 설치를 시도합니다."),
    (
        "04_load.py",
        "4. vLLM Qwen3.5-9B FP8 로드",
        "첫 실행에서 공식 모델 SHA를 고정합니다. 모델 다운로드에는 시간이 걸립니다.",
    ),
    (
        "05_pilot.py",
        "5. 20건 표본 검증",
        "자료별 10건. 결과·근거·속도를 확인합니다. 비교 라벨은 AI 초안이며 사람 정답이 아닙니다.",
    ),
    (
        "06_full.py",
        "6. 전체 라벨링·재개",
        "표본 확인 후 RUN_FULL=True. 동일 RUN_NAME·설정으로 다시 실행하면 저장된 ID를 건너뜁니다.",
    ),
    (
        "07_results.py",
        "7. 결과·커버리지 확인",
        "오류·긴 입력·보류는 성공으로 숨기지 않습니다. 의미 판단도 사람 검토 전 AI 초안입니다.",
    ),
]


def cell(kind: str, content: str) -> dict:
    result = {
        "cell_type": kind,
        "id": hashlib.sha256(content.encode()).hexdigest()[:12],
        "metadata": {},
        "source": content.splitlines(keepends=True),
    }
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


def main() -> None:
    intro = """# ThinkGuard — Qwen3.5-9B 의미 재라벨링

**준비물:** 이 노트북, `thinkguard_colab_vllm_bundle.zip`, Google Drive, Colab L4 GPU.
위에서부터 차례대로 실행하세요. 첫 표본 검증을 마친 뒤 전체 실행을 켭니다.

- 모델: `RedHatAI/Qwen3.5-9B-FP8-dynamic`, vLLM, non-thinking, 텍스트 전용.
- L4 시작 설정: 배치 8, GPU 메모리 비율 0.85, 최대 길이 7,168, eager 실행.
- 설치가 PyTorch를 변경할 수 있습니다. 셀 3에서 중단되면 세션을 다시 시작하고 셀 1부터 실행하세요.
- 원본: StudyChat 16,851건 + RECIPE4U 1,913건. 기존 주석은 덮어쓰지 않습니다.
- 결과: `MyDrive/ThinkGuard_NLP/qwen35_9b_vllm_fp8_v1/`에 저장합니다.
- 10건마다 해시가 붙은 불변 체크포인트 저장. 강제 종료 시 최대 9건을 다시 처리할 수 있습니다.
- 모델·입력·프롬프트·실행 설정이 바뀌면 다른 실행 이름을 사용해야 합니다.
- 현재 입력 한도 6,000토큰. 넘는 대화는 잘라 읽지 않고 `context_overflow`로 기록합니다.
- `ok`는 JSON·인용 검증 통과라는 뜻입니다. 라벨 정확성·사람 검토 완료를 보증하지 않습니다.
- 원본·학생 발화는 공개 저장소나 공개 노트북 출력에 올리지 말고 개인 Drive에 보관하세요.

GPU 할당·CUDA 호환성과 실제 속도는 연결 후 확인합니다. 이 노트북은 로컬에서
구문·입력·근거 검증·체크포인트 재개를 검사했으며 아직 GPU 추론으로 검증하지 않았습니다.

공식 참고: [모델 카드](https://huggingface.co/Qwen/Qwen3.5-9B),
[vLLM Qwen3.5 공식 레시피](https://github.com/vllm-project/recipes/blob/main/models/Qwen/Qwen3.5-9B.yaml).
"""
    cells = [cell("markdown", intro)]
    for filename, title, note in SECTIONS:
        source = (CELLS / filename).read_text(encoding="utf-8")
        ast.parse(source, filename=filename)
        cells.extend([cell("markdown", f"## {title}\n\n{note}\n"), cell("code", source)])
    cells.append(
        cell(
            "markdown",
            """## 연결이 끊겼을 때

GPU 런타임을 다시 연결하고 셀 1부터 실행합니다. Drive ZIP과 모델 SHA는 재사용합니다.
모델 캐시는 Colab 임시 디스크여서 새 런타임에서는 다시 내려받을 수 있습니다.
표본과 전체 결과는 Drive에 남습니다. 설정이 같으면 이미 체크포인트된 행은 재처리하지 않습니다.
중단 시 노트북의 정지 버튼은 finally 저장을 시도합니다. 강제 종료에서는 마지막 9건이 유실될 수 있습니다.

`context_overflow`, `oom`, `invalid_output`은 의미 검토 성공이 아니며 errors.json으로 모읍니다.
오류 행은 자동으로 무한 재시도하지 않습니다. 원인 수정 후 별도 실행으로 재검토해야 합니다.
전체 커버리지의 모든 status가 ok여야 모든 행이 의미 추론을 통과한 상태입니다.
라벨 null 보류는 ok인 행에도 남을 수 있으며 별도 사람 검토 대상입니다.
패키지·PyTorch가 달라 재개가 거부되면 기존 결과를 보존하고 새 RUN_NAME으로 시작하세요.
""",
        )
    )
    notebook = {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"name": OUT.name, "provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Notebook: {OUT}; cells={len(cells)}; GPU not executed")


if __name__ == "__main__":
    main()
