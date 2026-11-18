# Colab GPU 의미 라벨링 실행 안내

상태: **노트북·입력 준비, GPU 추론 미실행**. 작성일: 2026-11-16.

## 준비한 파일

1. `notebooks/thinkguard_qwen35_9b_labeling.ipynb`
2. `data/raw/colab_bundle/thinkguard_colab_bundle.zip`

Colab에서 첫 파일을 열고 GPU 런타임을 연결한다. 두 번째 파일은 노트북 셀 2에서 업로드한다.
공개 GitHub나 공개 노트북에 원문 ZIP을 올리지 않는다. 개인 Drive에 한 번만 보관하면 된다.
원본 파일을 다시 내려받거나 Hugging Face의 StudyChat 권한을 Colab에 전달할 필요는 없다.
확보한 원본에서 입력을 이미 구성했고 원본 해시를 검증한 패키지를 사용한다.

## 노트북 실행 순서

1. GPU·VRAM 확인. CPU로 몰래 대체하지 않으며 14 GiB 미만이면 설정 점검을 요청한다.
2. Drive 연결, ZIP 업로드/재사용, 내부 파일 해시 검사.
3. 추론 패키지 설치, 버전 기록/재사용.
4. 공식 Qwen3.5-9B 모델 리비전 고정 후 bitsandbytes NF4 4비트 로드.
5. 각 자료 10건, 총 20건 표본 추론·JSON/근거 검사·처리시간 측정.
6. 결과를 확인한 뒤 RUN_FULL=True로 전체 18,764건을 처리.
7. 커버리지·오류·보류·최종 JSONL을 저장.

4비트는 **로드 시 양자화**다. Ollama의 6.6GB GGUF를 쓰는 구성이 아니다.
공식 Transformers 원본 가중치를 내려받으므로 실제 다운로드 크기·임시 디스크 사용은 더 크다.
모델 다운로드는 노트북의 GPU 로드 셀에서 시작한다. 로컬 PC에는 모델을 설치하지 않았다.
GPU 종류에 따른 속도·호환성·실제 메모리는 아직 측정하지 않았다.

## 입력·라벨 규칙

입력 패키지에는 원본 의도 라벨이나 기존 목표 정답이 들어가지 않는다.
진단용 기존 AI 주석 200건은 별도 references.jsonl로 분리했다.
표본 진단 입력은 기존 AI 주석 당시의 이력 범위를 보존하며, 전체 입력과 구성이 다를 수 있다.
비교 일치도는 사람 정답에 대한 정확도·Macro-F1이 아니다.

전체 RECIPE4U 입력은 이전 행들의 chatgpt_before와 학생 발화를 모두 시간순으로 보존한다.
현재 행의 chatgpt_after, 시점 미확인 essay, 미래 학생 발화는 제외한다.
이는 기존 초기 파이프라인이 이전 학생 발화와 직전 AI만 사용했던 것보다 풍부한 이력이다.
StudyChat은 마지막 user가 현재 prompt와 일치하는지 검사한 뒤 그 이전 대화를 사용한다.
입력 내부 명령·URL·코드는 분석 대상이며 실행하거나 원격 링크를 열지 않는다.

프롬프트는 기존 v0.1·v0.3 의미 기준을 명시한다.
출력은 라벨 3종, 현재 시도, 문맥 결손, 이전 근거의 같은 문항 여부, 항목별 이유와 원문 인용이다.
양성 시도 근거는 학생 발화의 정확한 부분 문자열과 턴 위치로 검증한다.
실패 시 한 번 수정 요청 후에도 유효하지 않으면 invalid_output으로 기록한다.
추론은 non-thinking·greedy로 설정하고 모델·패키지·프롬프트·입력·설정 해시를 남긴다.
이 설정은 원 제작자의 공개 벤치마크 설정과 동일하지 않다.

## 저장·재개

개인 Drive: `MyDrive/ThinkGuard_NLP/qwen35_9b_trial_v1/`.

- `pilot/`: 표본 원문 검토·진단·체크포인트.
- `full/part-*.jsonl`: 10건마다 생성되는 불변 체크포인트.
- `full/annotations.jsonl`: 저장된 결과를 모은 파일, 재개 시 체크포인트가 기준이다.
- `full/progress.json`: 마지막 저장 진행 상태.
- `full/errors.json`, `full/uncertain.json`, `full/coverage.json`: 결과 셀에서 생성.
- 모델 SHA·패키지 버전·실행 설정·GPU 정보도 함께 기록.

재접속하면 같은 ZIP·RUN_NAME·설정으로 셀 1부터 실행한다.
같은 원본 ID의 체크포인트는 건너뛴다. 강제 종료는 마지막 미저장 최대 9건을 재처리할 수 있다.
프로그램 정지는 finally에서 미저장 결과를 Drive에 저장하려고 시도한다.
Drive의 임시 파일은 재개 시 무시하고 완성된 조각 파일은 SHA-256을 확인한다.
원본·프롬프트·모델 리비전·추론 설정이 바뀌면 재개를 거부해 결과 혼합을 막는다.
다른 GPU가 재할당돼도 같은 계산 dtype·패키지·설정이면 재개할 수 있다.
Colab 자체의 PyTorch 버전 등이 바뀌었다면 별도 RUN_NAME과 결과 병합 검토가 필요할 수 있다.

## 완료 조건과 한계

긴 입력은 6,000토큰 한도를 넘으면 context_overflow로 기록한다. 조용히 잘라 읽지 않는다.
OOM은 별도 오류다. 이런 행은 의미 검토 성공으로 세지 않으며 GPU/문맥 설정을 조정해 재검토한다.
오류 행도 저장하므로 재접속 때 무한 실패를 반복하지 않는다. 수정 후 별도 재시도 실행이 필요하다.
전체 행 수와 status=ok 수가 같아야 전체 행이 추론·형식 검증을 통과한 것이다.
ok에도 판단 보류(null)가 남을 수 있고, 이는 별도 검토 대상이다.
결과 전체는 qwen_semantic_draft이며 human_reviewed=false, gold_eligible=false다.

## 로컬 검증

GPU 없는 로컬에서 근거 혼입·없는 인용·문항 경계·문자열 boolean 거부,
체크포인트 손상·설정 변경·중단/재개·중복 방지 검사를 수행한다.
노트북의 모든 코드 셀은 Python 구문을 검사한다. 코드에 실행 결과나 원문을 포함하지 않는다.
GPU 로드·생성 속도·실제 분류 품질은 GPU 연결 후 검증한다.

공식 구현 참고:
[Qwen 모델 카드](https://huggingface.co/Qwen/Qwen3.5-9B),
[Transformers Qwen3.5](https://huggingface.co/docs/transformers/en/model_doc/qwen3_5),
[bitsandbytes](https://huggingface.co/docs/transformers/en/quantization/bitsandbytes).
