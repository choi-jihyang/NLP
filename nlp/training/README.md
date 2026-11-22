# NLP 학습·실험 파이프라인 (1~7단계)

판단 모델 학습 과정과 힌트 생성 실험 코드. 서비스에서 쓰는 분류기는 `nlp/thinkguard_nlp/` 이고, 사용법은 [../README.md](../README.md).

```
nlp/training/
├── scripts/01_join_studychat.py   # 라벨 CSV + StudyChat 원본 조인
├── scripts/02_translate_ko.py     # 한국어 번역 (Claude API 또는 vLLM/Ollama)
├── scripts/03_baseline_tfidf.py   # TF-IDF + LR 기준선
├── scripts/04_train_bge_m3.py     # bge-m3 판단 모델 학습
├── scripts/05_predict.py          # 학습된 판단 모델로 split 전체 확률 추출
├── scripts/06_tune_policy.py      # 운영 임계값 (false_unlock ↔ unnecessary_check)
├── scripts/07_respond.py          # 판단 → 정책 → 힌트 생성 LLM 응답 (데모·일괄 생성)
├── scripts/judge.py               # 판단 모델 추론 모듈
├── scripts/policy.py              # 응답 모드와 힌트 생성 프롬프트
├── scripts/common.py              # 공통: 데이터 로드, 입력 구성, 평가 지표
├── notebooks/                     # Colab·Kaggle 노트북 (번역, 학습)
├── kaggle_upload/                 # Kaggle 데이터셋 업로드용 zip
├── results/                       # 실험 결과
├── data/raw/                      # StudyChat 원본 (직접 다운로드)
├── data/joined/                   # 1단계 결과 (영어)
└── data/ko/                       # 2단계 결과 (한국어)
```

## 0. 준비

```bash
cd nlp/training
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

StudyChat은 gated 데이터셋이라 직접 해야 하는 단계가 있다.
1. https://huggingface.co/datasets/wmcnicho/StudyChat 에 로그인하고 약관에 동의한다.
2. `hf auth login` 으로 본인 토큰을 등록한다.
3. 다운로드한다 (약 626MB):

```bash
hf download wmcnicho/StudyChat data.jsonl --repo-type dataset --local-dir data/raw
```

## 1단계: 조인

```bash
python scripts/01_join_studychat.py --studychat data/raw/data.jsonl --labels-dir <라벨 CSV 폴더> --out-dir data/joined
```

출력된 내용에서 다음을 꼭 확인한다.
- **turn offset별 매칭률**: offset 0이 ~100%여야 한다. `source_id`의 턴 번호를 StudyChat `interactionCount`로 가정했는데, 다른 offset이 더 높게 나오면 `--turn-offset`을 바꿔서 다시 실행한다.
- **학생ID 불일치**: 0이어야 정상이다.
- **무작위 샘플 5개**: 라벨(답 요청 여부, 시도 여부)이 발화 내용과 맞는지 눈으로 확인한다. 안 맞으면 라벨링 담당 팀원에게 턴 번호를 어떻게 셌는지 물어본다.

옵션: `--history-msgs 4`(이전 메시지 몇 개를 남길지), `--max-chars 800`(이전 메시지 1개당 최대 글자 수). 기본값은 번역량을 줄이도록 맞춰 두었다.

## 2단계: 번역 – 무료 (Colab + vLLM, 추천)

1. Google Drive `내 드라이브/ThinkGuard_model/`에 `scripts/02_translate_ko.py`와 `data/joined/*.jsonl`(약 29MB)을 올린다.
2. [notebooks/colab_translate_ko.ipynb](notebooks/colab_translate_ko.ipynb)를 Colab에서 열고, 런타임을 **T4 GPU**로 바꾼 뒤 위에서부터 실행한다.
3. 5번 셀(시험 번역 15행)에서 품질을 확인한 다음 6번 셀(전체 번역, 약 3~7시간)을 실행한다.
4. 끝나면 Drive의 `data/ko/`를 이 폴더의 `data/ko/`로 내려받는다.

- 기본 번역 모델은 EXAONE 3.5 7.8B AWQ이다. 대안으로 Qwen2.5-7B-Instruct-AWQ, 더 빠른 EXAONE 2.4B를 쓸 수 있다.
- Colab 무료 GPU는 하루 사용 시간이 제한된다. 끊기면 다음에 같은 셀을 다시 실행해서 이어서 번역하면 된다.
- 로컬 Mac(Ollama)에서도 `--backend openai --base-url http://localhost:11434/v1 --model exaone3.5:7.8b`로 실행할 수 있지만, 며칠이 걸린다.

## 2단계: 번역 – 유료 (Claude API)

```bash
export ANTHROPIC_API_KEY=...                 # 본인 키
python scripts/02_translate_ko.py --dry-run  # 분량과 예상 비용만 확인 (호출 없음)
python scripts/02_translate_ko.py --limit 20 # 소량 시험 → data/ko/review_sample.csv 확인
python scripts/02_translate_ko.py            # 전체 번역 (중단돼도 다시 실행하면 이어서 함)
```

- 기본 모델은 `claude-opus-5-5`(effort low)이고, 현재 설정 기준 Haiku 5.5로 전체를 번역하면 약 $4이다. 비용을 줄이려면 `--model claude-haiku-5-5`나 `--model claude-sonnet-5-5`로 바꾸고, 같은 20개로 품질을 비교한 뒤 고른다.
- `--no-assistant`를 주면 이전 대화의 AI 답변은 번역하지 않는다. AI 답변이 길어서 비용 대부분을 차지하기 때문이다.
- 코드 블록과 인라인 코드는 자리표시자로 보호한 뒤 번역해서 원문 그대로 유지된다.
- `translation_ok=false`인 행은 번역에 실패해 영어 원문이 남아 있다. 학습 시 제외하거나 다시 실행한다. 실패한 항목만 재시도된다.
- **검수**: `data/ko/review_sample.csv`(100행)를 열어서 번역 후에도 라벨이 맞는지 `label_still_valid` 열에 O/X로 표시한다.

## 출력 형식 (jsonl 한 줄)

```json
{"id": "<chatId>:<turn>", "split": "train", "lang": "ko",
 "message": "현재 학생 발화", "history": [{"role": "student|assistant", "text": "..."}],
 "labels": {"is_learning_context": true, "requests_complete_answer": false, "has_self_attempt_evidence": true},
 "message_en": "(ko 파일만) 영어 원문", "translation_ok": true}
```

학습할 때는 `data/joined/train.jsonl`(영어)과 `data/ko/train.jsonl`(한국어)을 합쳐 쓴다.

## 3단계: TF-IDF 기준선

```bash
python scripts/03_baseline_tfidf.py                                              # 영어만
python scripts/03_baseline_tfidf.py --data-dirs data/joined data/ko --tag en_ko  # 번역 후
```

Mac에서 1분 정도 걸린다. 영어 test 결과는 현재 발화만 넣었을 때 request F1 0.62, attempt F1 0.61, learning=false F1 0.69다.

## 4단계: bge-m3 판단 모델 (Colab T4)

[notebooks/colab_train_bge_m3.ipynb](notebooks/colab_train_bge_m3.ipynb)를 쓴다. Drive에 `scripts/`(common.py 포함)와 `data/joined`, `data/ko`를 올려두고 실행한다.

- 입력: 현재 발화 + 이전 대화 (`--view full`) 또는 현재 발화만 (`--view message`), 최대 512토큰. 이전 대화가 길면 이전 대화 쪽부터 잘린다.
- 임계값은 valid 셋에서 정한다. learning은 false를 찾는 F1 기준, 나머지는 true F1 기준이다. test 셋에는 한 번만 적용한다.
- test 점수는 영어(en)와 한국어(ko)로 나뉘어 나온다. 실제 한국어 성능은 팀이 만드는 한국어 평가셋으로 따로 잰다.
- `--save-model`을 켜면 `best_model/`에 모델과 함께 `thinkguard.json`(임계값, 입력 방식)이 저장된다. 추론할 때 둘 다 필요하다.

### Kaggle에서 학습하기 (Colab GPU가 막혔을 때)
[notebooks/kaggle_train_bge_m3.ipynb](notebooks/kaggle_train_bge_m3.ipynb)를 쓴다. Kaggle은 무료 GPU를 주당 약 30시간 준다.
1. 업로드 묶음을 만든다 (스크립트와 데이터가 바뀌면 다시 만든다):
   ```bash
   zip -q kaggle_upload/thinkguard_data.zip scripts/common.py scripts/03_baseline_tfidf.py scripts/04_train_bge_m3.py scripts/05_predict.py scripts/06_tune_policy.py scripts/judge.py scripts/policy.py data/joined/{train,valid,test}.jsonl data/ko/{train,valid,test}.jsonl
   ```
2. Kaggle → Datasets → New Dataset에서 zip을 **Private**으로 올린다.
3. 노트북을 Import하고 오른쪽 패널에서 Add Input(데이터셋), Accelerator **GPU T4 x2**, Internet **On**을 설정한다.
4. **Save Version → Save & Run All**로 돌리면 브라우저를 닫아도 끝까지 돈다. 결과는 Output 탭에 남는다.

### 평가 지표
- **request / attempt F1**: 주 지표.
- **learning=false F1**: 학습 맥락 라벨은 98%가 true라서 true 쪽 F1은 의미가 없다. 대신 드문 false(인사, 잡담)를 얼마나 잘 찾는지 본다.
- **false_unlock**: 답을 요청했고 시도가 없는 학생을 "시도 있음"으로 잘못 판단한 수. 서비스에서는 답을 열어주는 실수라서 가장 중요하다.
- **unnecessary_check**: 시도가 있는데 "시도 없음"으로 판단해 다시 확인 질문을 하게 되는 수.
- **mean_label_macro_f1**: 라벨마다 true·false F1 평균을 내고 라벨 3개를 다시 평균한 값. 팀원 모델과 비교할 때 쓴다.

## 5~6단계: 운영 임계값 정하기

F1 최대 임계값은 두 실수를 같은 무게로 본다. 서비스에서는 false_unlock이 더 비싸므로, 허용할 false_unlock 비율을 정하고 그 안에서 unnecessary_check가 가장 적은 attempt 임계값을 고른다. **반드시 valid로 정하고 test에는 확인만 한다.**

```bash
cd scripts
# (04 최신 버전으로 학습했으면 valid_probs.npy 가 이미 있으니 05는 건너뛴다)
python 05_predict.py --model-dir ../results/bge_m3/en_ko_full/best_model --data-dirs ../data/joined ../data/ko --split valid
python 06_tune_policy.py --probs-dir ../results/bge_m3/en_ko_full --split valid --data-dirs ../data/joined ../data/ko \
    --base-thresholds ../results/bge_m3/en_ko_full/best_model/thinkguard.json --max-false-unlock 0.25
python 06_tune_policy.py --probs-dir ../results/bge_m3/en_ko_full --split test --data-dirs ../data/joined ../data/ko \
    --apply ../results/bge_m3/en_ko_full/policy_thresholds.json
```

결과로 `policy_thresholds.json`이 생기고, 07단계에서 `--thresholds-file`로 쓴다.

**현재 확정값 (2026-11-22)**: false_unlock 25% 이하 목표 → attempt 임계값 **0.73** (learning 0.05, request 0.55). test 결과 false_unlock 35/194 (18%), unnecessary_check 134/332 (40%), mean_label_macro_f1 0.792. 이 값은 `best_model/thinkguard.json`의 `thresholds`에도 반영해 두어서 `--thresholds-file` 없이 모델만 불러와도 적용된다 (F1 최대값 0.43은 `thresholds_f1_max`에 보관). 한국어 실사용 평가셋도 같은 jsonl 형식으로 만들면 05로 평가한다.

## 7단계: 응답 정책과 힌트 생성

| 판단 결과 | 모드 | 응답 |
|---|---|---|
| 학습 맥락 아님 | `off_topic` | 1~2문장 응대, 학습 질문으로 유도 |
| 학습 맥락, 완성된 답 요청 아님 | `explain` | 질문 범위 안에서 설명. 과제 해답 전체는 쓰지 않음 |
| 답 요청, 시도 없음 | `nudge` | 답 없이 확인 질문 1개 + 첫 힌트 (반복될수록 방향 → 단계 → 빈칸 골격) |
| 답 요청, 시도 있음 | `feedback` | 시도에서 맞은 점·틀린 점, 다음 한 단계 힌트 |

교수자 정책 옵션: `--no-first-hint`(nudge에서 힌트 없이 확인 질문만), `--final-answer never|after_attempt`(시도 후 최종 답 공개 여부). 프롬프트는 `scripts/policy.py`에 있다.

힌트 생성 LLM은 OpenAI 호환 서버면 된다. Mac(16GB)에서는 Ollama가 가장 간단하다.

```bash
brew install ollama && ollama serve        # 다른 터미널에서
ollama pull qwen3:8b && ollama pull exaone3.5:7.8b
cd scripts
python 07_respond.py --labels 1,1,0 --message "BFS 코드 전체 짜줘" --dry-run         # 프롬프트만 확인
python 07_respond.py --model-dir ../results/bge_m3/en_ko_full/best_model \
    --thresholds-file ../results/bge_m3/en_ko_full/policy_thresholds.json --interactive  # 대화형 데모
# Qwen3 vs EXAONE 비교: 정답 라벨로 모드를 정하고 같은 40문장 생성 → CSV에서 정답누출·적절성 표시
python 07_respond.py --batch ../data/ko/test.jsonl --use-gold --sample 40 --llm-model qwen3:8b --out ../results/gen/qwen3.csv
python 07_respond.py --batch ../data/ko/test.jsonl --use-gold --sample 40 --llm-model exaone3.5:7.8b --out ../results/gen/exaone.csv
```

- Qwen3의 생각 모드는 자동으로 끈다 (Ollama는 `reasoning_effort="none"`, vLLM 서버면 `--vllm`을 준다).
- **선택 결과 (2026-11-22)**: 같은 test 40문장 비교에서 Qwen3 8B가 첫 생성 정답 누출 의심 1건(EXAONE 17건), 응답 길이 중앙값 200자(EXAONE 860자)로 더 규칙을 잘 지켜 **qwen3:8b**를 쓴다. 결과는 `results/gen/*.csv`.
- 알려진 한계: 이전 대화에 글이 있는 상태에서 감상문·에세이를 대신 써 달라는 요청은 프롬프트로 막히지 않는다.
- `leak_flags` 열은 답을 열면 안 되는 모드에서 긴 코드 블록이나 "정답은" 같은 표현이 나온 경우를 표시한다. 자동 판정이 아니라 검토할 곳을 알려 주는 표시다.

