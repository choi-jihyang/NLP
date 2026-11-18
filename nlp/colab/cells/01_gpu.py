import torch

if not torch.cuda.is_available():
    raise RuntimeError("런타임 → 런타임 유형 변경 → GPU로 설정한 뒤 다시 실행하세요.")
gpu = torch.cuda.get_device_properties(0)
print("GPU:", gpu.name)
print("VRAM GiB:", round(gpu.total_memory / 2**30, 2))
print("PyTorch:", torch.__version__, "CUDA:", torch.version.cuda)
if gpu.total_memory / 2**30 < 14:
    raise RuntimeError("이 노트북의 9B 시험 설정에는 14 GiB 이상 GPU를 권장합니다. 설정을 먼저 점검하세요.")
