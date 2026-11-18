# ruff: noqa: F821
from huggingface_hub import HfApi
from inference_vllm import Annotator, load_model
from journal import atomic_json
from runner import configuration

MODEL_ID = "RedHatAI/Qwen3.5-9B-FP8-dynamic"
if (WORK / "restart_required.json").exists():
    raise RuntimeError("설치 후 세션을 다시 시작하고 셀 1부터 재실행하세요.")
if "model" in globals():
    raise RuntimeError("모델이 이미 로드되어 있습니다. 다시 로드하려면 세션을 다시 시작하세요.")
revision_file = PROJECT_DIR / f"{RUN_NAME}_model_revision.json"
if revision_file.exists():
    model_pin = json.loads(revision_file.read_text(encoding="utf-8"))
    if model_pin["model_id"] != MODEL_ID:
        raise ValueError("Model ID changed; use a new RUN_NAME")
else:
    model_pin = {"model_id": MODEL_ID, "revision": HfApi().model_info(MODEL_ID).sha}
    atomic_json(revision_file, model_pin)
print("고정 모델:", model_pin)
model, tokenizer, model_metadata = load_model(MODEL_ID, model_pin["revision"])
annotator = Annotator(model, tokenizer, max_input_tokens=6000, max_new_tokens=768)
run_config = configuration(manifest, model_metadata, annotator)
run_root = PROJECT_DIR / RUN_NAME
run_root.mkdir(exist_ok=True)
atomic_json(run_root / "current_hardware.json", model_metadata)
print("추론 엔진:", model_metadata["engine"], "배치 크기:", annotator.batch_size)
print("GPU 메모리 사용 비율:", model_metadata["engine_settings"]["gpu_memory_utilization"])
print("로드 완료. 먼저 다음 셀의 표본 검증을 실행하세요.")
