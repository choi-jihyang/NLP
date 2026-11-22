# NLP — 판단 모델(분류기)과 힌트 생성

```
nlp/
├── thinkguard_nlp/    서비스용 분류기 — 백엔드가 쓰는 classify() (연동 계약 그대로)
├── server.py          분류기 HTTP 서버 (CLASSIFIER=http)
├── tests/             연동 계약 출력 테스트 (모델 없이 실행)
├── models/            판단 모델 폴더를 여기에 넣는다 (git 제외, 약 2.3GB)
└── training/          학습·평가·힌트 생성 실험 코드 → training/README.md
```

## 판단 모델

- **모델**: `BAAI/bge-m3`(다국어) 파인튜닝, 라벨 3개 multi-label 분류
- **입력**: 현재 학생 발화 + 이전 대화 최근 4개
- **학습 데이터**: StudyChat 라벨 8.7k행 영어 원문 + 한국어 번역본(Claude Haiku)
- **임계값**: learning 0.05 / request 0.55 / attempt 0.73
  - attempt는 F1 최대값(0.43) 대신 0.73으로 올렸다. 시도 없는 학생에게 다음 단계를 여는 실수(false_unlock)가 33%에서 18%로 줄고, 시도한 학생의 약 40%가 확인 질문을 한 번 더 받는다.
- **성능** (StudyChat test, `mean_label_macro_f1`): 영어 0.789 / 한국어 번역본 0.795
- **confidence**: 정책에 실제로 쓰인 라벨들의 판단 여유(임계값에서 떨어진 정도) 중 최솟값이다. 백엔드 기본값(`CLASSIFIER_MIN_CONFIDENCE=0.5`)에서는 valid 기준 약 9%가 되묻기(ASK_ATTEMPT)로 간다. `uncertain`은 항상 false다.

### 써 보기
1. 공유받은 `best_model` 폴더를 `nlp/models/bge_m3_en_ko/`로 넣는다. 안에 `thinkguard.json`, `model.safetensors`, 토크나이저 파일이 있어야 한다. 다른 위치에 두려면 `THINKGUARD_MODEL_DIR`를 지정한다.
2. 설치와 테스트
   ```bash
   cd nlp
   python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -e ".[model,server,dev]"
   pytest -q tests                                          # 계약 형식 테스트 (모델 없이)
   python -c "from thinkguard_nlp.classifier import classify; print(classify('BFS 함수 전체 코드 짜줘', []))"
   ```
3. 백엔드에 붙이기 ([연동 계약](../docs/spec/integration-contract.md))
   - **module**: `cd backend && .venv/bin/pip install -e "../nlp[model]"` 후 `backend/.env`에 `CLASSIFIER=module`
   - **http**: `cd nlp && uvicorn server:app --port 8001` 후 `backend/.env`에 `CLASSIFIER=http`
   - 모델은 import할 때 한 번만 불러온다 (Mac M2 기준 약 6초, 요청 1건 0.02~0.5초).

### 알려진 한계
- **말로만 설명한 시도는 잘 못 잡는다.** 코드 없이 한국어 문장으로만 설명한 시도는 시도 근거로 판단하지 못하는 경우가 많다.
  - 예: 연동 계약 예시인 "D=b²−4ac 에 넣어서 16−4k 까지 했어요" → "이제 정답 알려줘"도 시도 없음으로 판단한다.
- **코드를 붙이고 "고쳐줘"라고 하면** 답 요청과 시도를 모두 false로 보는 경우가 있다.
- **해봤다는 주장만 하는 요청을 놓친다.** "해봤는데 안 돼요 답 주세요"를 답 요청 false로 판단했다.
- **이전 대화 입력에 AI 답변도 들어간다.** 학습 데이터 입력 형식이 그랬기 때문이다. 불변식 I4(시도 근거는 학생 메시지에서만)는 라벨 기준으로는 지켜지지만, 모델 입력 단계에서 강제되지는 않는다.
- 위 수치는 번역본 기준이다. 실제 한국어 성능은 팀 한국어 평가셋(300문장)으로 다시 잰다.

## 힌트 생성 LLM

- **추천**: `qwen3:8b` (Ollama).
  - 같은 test 40문장 비교에서 첫 생성 정답 누출 의심이 1건이었다 (EXAONE 3.5 7.8B는 17건).
  - 응답 길이 중앙값도 200자로 짧았다 (EXAONE은 860자).
- **백엔드 연결 시 주의**: Qwen3는 기본으로 생각 모드가 켜져 있다. 그대로 두면 느리고, 생각에 토큰을 다 써서 빈 응답이 나올 수 있다. `backend/app/llm/ollama.py` 요청에 `"think": false`를 넣어야 한다 (웹 담당 확인 필요).
- 응답 정책·프롬프트 실험 코드와 일괄 생성 비교: [training/README.md](training/README.md) 7단계
  - `training/scripts/policy.py`: 4가지 모드 프롬프트, 정답 누출 감지 후 재생성
  - `training/scripts/07_respond.py`: 판단 → 정책 → LLM 데모

### 힌트 생성만 바로 써 보기 (판단 모델 없이)
```bash
ollama pull qwen3:8b
cd nlp/training && pip install -r requirements.txt && cd scripts
python 07_respond.py --labels 1,1,0 --message "BFS 함수 전체 코드 짜줘"        # 학습맥락,답요청,시도
python 07_respond.py --labels 1,1,1 --message "visited 없이 큐만 썼더니 무한루프가 돌아요. 다음엔 뭘 해야 돼요?"
python 07_respond.py --model-dir ../../models/bge_m3_en_ko --interactive          # 판단 모델까지 연결한 대화형
```
