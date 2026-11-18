"""Create a 3,000-row tail package, teammate notebook and owner handoff notebook."""

import argparse
import ast
import sys
from pathlib import Path

from colab_notebook_io import notebook
from team_bundle import create_team_bundle, print_bundle_summary

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "nlp/colab"
TEMPLATES = MODULES / "templates"
sys.path.insert(0, str(MODULES))

OUT = ROOT / "data/raw/colab_team_last3000"
BASE = ROOT / "data/raw/colab_bundle"
NOTEBOOKS = ROOT / "notebooks"


def main(long_context=False):
    global OUT
    if long_context:
        OUT = OUT.with_name("colab_team_last3000_long32k")
    bundle_name = "thinkguard_team_last3000_long32k.zip" if long_context else "thinkguard_team_last3000.zip"
    notebook_name = "thinkguard_team_last3000_long32k.ipynb" if long_context else "thinkguard_team_last3000.ipynb"
    assignment, owner_count, archive_path = create_team_bundle(BASE, OUT, MODULES, bundle_name)
    upload = (MODULES / "cells/02_upload.py").read_text(encoding="utf-8")
    upload = upload.replace('MyDrive/ThinkGuard_NLP"', 'MyDrive/ThinkGuard_NLP_Team"')
    upload = upload.replace("qwen35_9b_vllm_fp8_v1", "qwen35_9b_vllm_team_last3000_v1")
    upload = upload.replace("thinkguard_colab_vllm_bundle.zip", "thinkguard_team_last3000.zip")
    upload = upload.replace("/content/thinkguard_colab_vllm", "/content/thinkguard_team_last3000")
    upload = upload.replace(', "진단 표본:", manifest["references"]', "")
    if long_context:
        upload = upload.replace("thinkguard_team_last3000.zip", bundle_name)
        upload = upload.replace("qwen35_9b_vllm_team_last3000_v1", "qwen35_9b_vllm_team_last3000_long32k_v1")
        upload = upload.replace("/content/thinkguard_team_last3000", "/content/thinkguard_team_last3000_long32k")
    upload += """
from team_split import assert_compatible
owner_config_path = PROJECT_DIR / "owner_run_config.json"
if not owner_config_path.exists():
    print("원래 작업자가 준 full 폴더의 run_config.json을 업로드하세요.")
    incoming = files.upload()
    if "run_config.json" not in incoming:
        raise ValueError("원래 full/run_config.json 파일이 필요합니다.")
    owner_config_path.write_bytes(incoming["run_config.json"])
owner_config = json.loads(owner_config_path.read_text(encoding="utf-8"))
assignment = json.loads((WORK / "assignment.json").read_text(encoding="utf-8"))
if owner_config["bundle_inputs_sha256"] != assignment["parent_inputs_sha256"]:
    raise ValueError("다른 원본의 실행 설정입니다.")
if owner_config["model"].get("engine") != "vllm":
    raise ValueError("vLLM 원본 실행 설정이 필요합니다.")
if owner_config["model"]["model_id"] != "RedHatAI/Qwen3.5-9B-FP8-dynamic":
    raise ValueError("예상한 FP8 모델이 아닙니다.")
print("담당 범위: 전체 순서 15,765~18,764번째 / 3,000건", assignment["team_counts"])
"""
    install = (MODULES / "cells/03_install.py").read_text(encoding="utf-8")
    start = install.index("if environment_file.exists():")
    end = install.index("subprocess.check_call", start)
    install = (
        install[:start]
        + (
            'requirements = [f"{name}=={version}'
            '" for name, version in owner_config'
            '["model"]["versions"].items()]\nrequ'
            'irements += ["safetensors", "senten'
            'cepiece"]\n'
        )
        + install[end:]
    )
    load = (MODULES / "cells/04_load.py").read_text(encoding="utf-8")
    start = load.index("revision_file =")
    end = load.index('print("고정 모델:', start)
    load = (
        load[:start]
        + """model_pin = {"model_id": MODEL_ID, "revision": owner_config["model"]["revision"]}
"""
        + load[end:]
    )
    load = load.replace(
        "run_config = configuration(manifest, model_metadata, annotator)",
        (
            "run_config = configuration(manifest"
            ", model_metadata, annotator)\nassert"
            "_compatible(owner_config, run_confi"
            "g)"
        ),
    )
    load = load.replace(
        'print("로드 완료. 먼저 다음 셀의 표본 검증을 실행하세요.")',
        'print("원본 실행과 모델·리비전·프롬프트·버전 일치 확인 완료.")',
    )
    if long_context:
        load = load.replace(
            'load_model(MODEL_ID, model_pin["revision"])',
            'load_model(MODEL_ID, model_pin["revision"], long_context=True)',
        )
        load = load.replace("max_input_tokens=6000", "max_input_tokens=32000")
        load = load.replace("run_config = configuration(", "annotator.batch_size = 1\nrun_config = configuration(")
        load = load.replace(
            "assert_compatible(owner_config, run_config)",
            'run_config["inference_profile"] = "team_long32k_v1"\nassert_compatible(owner_config, run_config)',
        )
        load = load.replace(
            'print("원본 실행과 모델·리비전·프롬프트·버전 일치 확인 완료.")',
            'print("원본 모델·프롬프트·버전 일치 확인. 입력 32,000 / 출력 768 / 동시 처리 1건.")',
        )
    execute = (TEMPLATES / "prepare_team_colab_execute.py.txt").read_text(encoding="utf-8")
    full = (TEMPLATES / "prepare_team_colab_full.py.txt").read_text(encoding="utf-8")
    export = (TEMPLATES / "prepare_team_colab_export.py.txt").read_text(encoding="utf-8")
    intro = (TEMPLATES / "team_intro.md.txt").read_text(encoding="utf-8").replace("{bundle_name}", bundle_name)
    if long_context:
        intro += (
            "\n\n**긴 입력 전용:** 입력 32,000 + 출력 768, "
            "엔진 최대 32,768토큰, 배치 1. 기존 6,000토큰 실행"
            "과 별도 폴더에 저장합니다. 먼저 세션을 다시 시작하세요. 32"
            ",000토큰을 넘는 입력은 여전히 미처리로 기록하며 절대 자르지"
            " 않습니다. 실제 L4 메모리 적합성은 첫 로드에서 확인해야 합"
            "니다. 병합 보고서에 두 실행의 입력 한도 차이를 남깁니다."
        )
    notebook(
        NOTEBOOKS / notebook_name,
        [
            ("markdown", intro),
            ("markdown", "## 1. L4 GPU 확인"),
            ("code", (MODULES / "cells/01_gpu.py").read_text(encoding="utf-8")),
            ("markdown", "## 2. Drive 연결, 팀원 ZIP 및 원 작업자 설정 업로드"),
            ("code", upload),
            (
                "markdown",
                (
                    "## 3. 원 작업자와 같은 패키지 설치\n\n재시작 안내가 나오면"
                    " **세션 다시 시작 후 1번부터 재실행**하세요. 파일은 Dr"
                    "ive에 보존됩니다."
                ),
            ),
            ("code", install),
            ("markdown", "## 4. 같은 리비전의 FP8 모델 로드"),
            ("code", load),
            ("markdown", "## 5. 담당 데이터 8건 표본 확인"),
            ("code", execute),
            (
                "markdown",
                ("## 6. 담당 3,000건 실행·재개\n\n재연결 시 같은 설정과 RUN_NAME으로 실행하면 저장된 ID를 건너뜁니다."),
            ),
            ("code", full),
            ("markdown", "## 7. 결과 ZIP 다운로드 및 원 작업자에게 전달"),
            ("code", export),
        ],
    )
    owner_resume = (TEMPLATES / "prepare_team_colab_owner_resume.py.txt").read_text(encoding="utf-8")
    (OUT / "owner_resume_first15764.py").write_text(owner_resume, encoding="utf-8")
    merge_source = (TEMPLATES / "prepare_team_colab_merge_source.py.txt").read_text(encoding="utf-8")
    (OUT / "owner_merge_team_results.py").write_text(merge_source, encoding="utf-8")
    # Also provide a notebook whose cells can be copied into the active original notebook.
    notebook(
        NOTEBOOKS / "thinkguard_owner_split_and_merge.ipynb",
        [
            (
                "markdown",
                (
                    "# 원 작업자용 분할·병합 셀\n\n**이 노트북 자체에서 실행하지"
                    " 말고 코드 셀을 현재 실행 중인 기존 노트북에 복사하세요.**"
                    " 기존 6번을 정지하고 저장 종료를 기다린 뒤 첫 셀을 실행합니"
                    "다. RUN_NAME·ZIP·run_config는 변경하지 않습"
                    "니다. 기존 7번은 전체 18,764건 기준이므로 병합 전에는 "
                    "미완료로 나오는 것이 정상입니다."
                ),
            ),
            ("markdown", "## 내 담당 앞 15,764건만 재개"),
            ("code", owner_resume),
            (
                "markdown",
                (
                    "## 팀원 완료 후 병합\n\n팀원 결과 ZIP과 함께 제공한 `t"
                    "eam_split.py`를 업로드하세요. 중복은 원 작업자 결과"
                    "를 유지하고 보고하며, 누락이 있으면 최종 파일 생성을 중단합니"
                    "다. 원 체크포인트는 덮어쓰지 않습니다."
                ),
            ),
            ("code", merge_source),
        ],
    )
    for name in ("owner_resume_first15764.py", "owner_merge_team_results.py"):
        ast.parse((OUT / name).read_text(encoding="utf-8"))
    (OUT / "team_split.py").write_bytes((MODULES / "team_split.py").read_bytes())
    print_bundle_summary(archive_path, owner_count, assignment)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--long-context", action="store_true")
    main(parser.parse_args().long_context)
