# ruff: noqa: F821
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

from google.colab import drive, files

drive.mount("/content/drive")
PROJECT_DIR = Path("/content/drive/MyDrive/ThinkGuard_NLP")
PROJECT_DIR.mkdir(parents=True, exist_ok=True)
RUN_NAME = "qwen35_9b_vllm_fp8_v1"  # 같은 설정으로 재개할 때는 바꾸지 마세요.
BUNDLE_NAME = "thinkguard_colab_vllm_bundle.zip"
BUNDLE = PROJECT_DIR / BUNDLE_NAME
WORK = Path("/content/thinkguard_colab_vllm")
WORK.mkdir(exist_ok=True)
if not BUNDLE.exists():
    print(f"제공받은 {BUNDLE_NAME} 하나를 업로드하세요.")
    uploaded = files.upload()
    if BUNDLE_NAME not in uploaded:
        raise ValueError("파일 이름을 확인하세요.")
    BUNDLE.write_bytes(uploaded[BUNDLE_NAME])
    del uploaded
shutil.copyfile(BUNDLE, WORK / "bundle.zip")
with zipfile.ZipFile(WORK / "bundle.zip") as archive:
    if archive.testzip() is not None:
        raise ValueError("ZIP checksum error")
    for name in archive.namelist():
        if Path(name).name != name or name.startswith("."):
            raise ValueError("Unexpected archive path")
    archive.extractall(WORK)
manifest = json.loads((WORK / "manifest.json").read_text(encoding="utf-8"))
for name, expected in manifest["files"].items():
    with (WORK / name).open("rb") as stream:
        observed = hashlib.file_digest(stream, "sha256").hexdigest()
    if observed != expected:
        raise ValueError(f"업로드 파일 검증 실패: {name}")
sys.path.insert(0, str(WORK))
print("원본 행 수:", manifest["counts"], "진단 표본:", manifest["references"])
print("Drive 저장 위치:", PROJECT_DIR)
