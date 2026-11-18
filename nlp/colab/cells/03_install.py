# ruff: noqa: F821
import importlib.metadata
import subprocess
import sys

packages = ["vllm", "torch", "transformers", "safetensors", "sentencepiece", "huggingface-hub"]
environment_file = PROJECT_DIR / "colab_vllm_package_versions.json"


def versions():
    result = {}
    for name in packages:
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


before = versions()
if environment_file.exists():
    previous = json.loads(environment_file.read_text(encoding="utf-8"))
    requirements = [f"{name}=={previous[name]}" for name in packages]
else:
    # Let the vLLM wheel select its matching PyTorch/CUDA dependencies.
    requirements = ["vllm>=0.17.0", "sentencepiece", "huggingface-hub"]
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--upgrade", *requirements])
installed = {name: importlib.metadata.version(name) for name in packages}
environment_file.write_text(json.dumps(installed, indent=2), encoding="utf-8")
print(installed)
restart_marker = WORK / "restart_required.json"
if before != installed:
    restart_marker.write_text(json.dumps({"pid": __import__("os").getpid()}), encoding="utf-8")
if restart_marker.exists():
    if json.loads(restart_marker.read_text())["pid"] == __import__("os").getpid():
        raise RuntimeError(
            "설치 완료. 런타임 → 세션 다시 시작 후 셀 1부터 다시 실행하세요. 지금 모델을 로드하지 마세요."
        )
    restart_marker.unlink()
print("vLLM 설치 확인 완료. 다음 셀을 실행하세요.")
