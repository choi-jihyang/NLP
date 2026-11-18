# Colab L4 vLLM 실행

- 노트북: `notebooks/thinkguard_qwen35_9b_vllm_labeling.ipynb`
- ZIP: `data/raw/colab_bundle/thinkguard_colab_vllm_bundle.zip`
- 모델: `RedHatAI/Qwen3.5-9B-FP8-dynamic` (Qwen3.5-9B의 FP8 양자화 버전)
- 엔진: vLLM >= 0.17.0, 텍스트 전용, 배치 8, eager, VRAM 비율 0.85.
- 입력 6,000 + 출력 768 토큰. 긴 입력은 자르지 않고 오류로 기록한다.

Colab의 **파일 → 노트북 열기 → 업로드**로 위 노트북을 연다.
기존 Transformers 모델이 메모리에 있다면 먼저 **런타임 → 세션 다시 시작**을 실행한다.
셀 1부터 실행하고 셀 2에서 새 ZIP을 올린다. 기존 ZIP과 파일 이름이 다르다.
셀 3은 vLLM wheel이 요구하는 PyTorch를 함께 설치한다. 기존 PyTorch 2.14.1을 강제로 유지하지 않는다.
설치 후 재시작 오류가 나오면 세션을 다시 시작하고 셀 1부터 재실행한다.
셀 4 모델 다운로드 후 셀 5의 20건 표본에서 근거·오류·평균 처리시간을 확인한다.
표본 검토 후에만 셀 6의 `RUN_FULL=True`를 설정한다.

Drive 결과는 `ThinkGuard_NLP/qwen35_9b_vllm_fp8_v1`에 저장한다.
기존 NF4 Transformers 실행과 모델·엔진·양자화가 달라 결과를 합쳐 재개하지 않는다.
체크포인트된 행만 건너뛴다. GPU 엔진 오류는 실행을 멈추며, 원인을 고친 뒤 동일 설정으로 재개한다.
배치가 완료되기 전에 강제 종료되면 해당 배치도 다시 계산한다.
설정 변경 시 새 RUN_NAME을 쓴다. 패키지 버전과 모델 SHA는 첫 설치/로드 시 고정한다.

로컬에서는 GPU 없이 계약·배치 순서·제한·재개 테스트를 수행한다.
실제 Colab L4에서 모델 로드·CUDA 호환성·처리량은 검증이 필요하다.

공식 근거: [vLLM Qwen3.5-9B 레시피](https://github.com/vllm-project/recipes/blob/main/models/Qwen/Qwen3.5-9B.yaml),
[vLLM GPU 설치](https://docs.vllm.ai/en/stable/getting_started/installation/gpu/).
