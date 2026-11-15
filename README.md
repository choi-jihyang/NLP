# ThinkGuard

교수자가 과목별 "학습용 AI"를 설정해 학생에게 배포하는 웹 서비스. AI는 정답을 주지 않고, 학생이 스스로 풀도록 단계별로 돕는다.
자연언어처리 수업 팀 프로젝트 (웹 2 · NLP 2) — 12/1 시연용 프로토타입.

- 문서: [docs/](docs/README.md) — 규칙(conventions) · 설계(planning) · 명세(spec)
- 현재 상태: 프로젝트 뼈대. 채팅 정책 분기(분류 → 정책 → 프롬프트)만 로직과 테스트가 있고, 화면은 자리만 있다.

## 구조
```
frontend/   React + TypeScript (Vite)
backend/    Python FastAPI
nlp/        NLP 팀 분류기 (thinkguard_nlp 패키지 + HTTP 서버)
docs/       conventions / planning / spec
```
자세히: [docs/planning/architecture.md](docs/planning/architecture.md)

## 로컬 실행

### 필요한 것
- Python 3.11 이상
- Node.js 20 이상
- (선택) [Ollama](https://ollama.com) — 실제 LLM으로 시험할 때만

### 백엔드
```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload
```
- 확인: http://localhost:8000/api/health → `{"status":"ok","llm_provider":"mock","classifier":"stub"}`
- API 문서(Swagger): http://localhost:8000/docs

### 프론트엔드
```bash
cd frontend
npm install
npm run dev
```
- 확인: http://localhost:5173 → 초록색 "백엔드 연결됨" 칩이 보이면 정상(백엔드가 켜져 있어야 함).
- `/api` 요청은 Vite가 백엔드(8000)로 넘겨 준다.
- 8000 포트를 다른 프로그램이 쓰고 있으면 백엔드를 다른 포트로 띄우고 프록시 대상을 지정한다.
  ```bash
  cd backend && .venv/bin/uvicorn app.main:app --reload --port 8010
  ```
  ```bash
  cd frontend && API_PROXY_TARGET=http://localhost:8010 npm run dev
  ```

### 테스트 · 검사
```bash
cd backend && .venv/bin/pytest && .venv/bin/ruff check .
```
```bash
cd frontend && npm run build && npm run lint
```

## 환경변수 (`backend/.env`)
| 변수 | 값 | 기본 | 설명 |
|---|---|---|---|
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///./thinkguard.db` | PostgreSQL 전환 시 URL만 교체 |
| `CORS_ORIGINS` | JSON 배열 | `["http://localhost:5173"]` | |
| `LLM_PROVIDER` | `mock` · `ollama` | `mock` | |
| `OLLAMA_BASE_URL` | URL | `http://localhost:11434` | |
| `OLLAMA_MODEL` | 모델 이름 | `qwen2.5:7b` | 후보: [integration-contract.md](docs/spec/integration-contract.md#2-llm-provider) |
| `CLASSIFIER` | `stub` · `module` · `http` | `stub` | |
| `CLASSIFIER_MODULE` | `모듈:함수` | `thinkguard_nlp.classifier:classify` | `CLASSIFIER=module`일 때 |
| `CLASSIFIER_URL` | URL | `http://localhost:8001/classify` | `CLASSIFIER=http`일 때 |
| `CLASSIFIER_MIN_CONFIDENCE` | 0.0–1.0 | `0.5` | 이보다 낮으면 "모호함"으로 보고 되묻기 |

## 실제 LLM 쓰기 (Ollama)
```bash
ollama pull qwen2.5:7b
```
`backend/.env`에서 `LLM_PROVIDER=ollama`로 바꾸고 백엔드를 다시 실행한다.

## NLP 분류기 교체
지금은 키워드 규칙 스텁(`CLASSIFIER=stub`)을 쓴다. NLP 팀 모델은 두 방식 중 하나로 붙인다. 계약: [docs/spec/integration-contract.md](docs/spec/integration-contract.md)

**방식 A — Python 모듈**
1. `nlp/thinkguard_nlp/classifier.py`의 `classify()`를 구현한다.
2. 백엔드 가상환경에 설치한다.
   ```bash
   cd backend && .venv/bin/pip install -e ../nlp
   ```
3. `backend/.env`에서 `CLASSIFIER=module`로 바꾼다.

**방식 B — HTTP 서버**
1. NLP 서버를 실행한다.
   ```bash
   cd nlp && pip install -e ".[server]" && uvicorn server:app --port 8001
   ```
2. `backend/.env`에서 `CLASSIFIER=http`로 바꾼다.

백엔드 코드는 고치지 않는다.
