# ThinkGuard

프로그래밍 과제용 학습 AI 튜터. 교수자가 과제마다 "AI가 어디까지 알려줄지"를 정하면, AI는 정답이나 완성 코드 대신 다음 한 단계만 돕고, 과제가 끝나면 학생이 AI 없이도 할 수 있는지 확인한다.
자연언어처리 수업 팀 프로젝트 (웹 2 · NLP 2) — 12/1 시연용 프로토타입.

- 문서: [docs/](docs/README.md) — 규칙(conventions) · 설계(planning) · 명세(spec)
- 화면 시안: [docs/planning/page_design.html](docs/planning/page_design.html) (브라우저로 열기)

## 지금 상태 (11/16)
| 부분 | 상태 |
|---|---|
| 화면 (`frontend/`) | **전체 구현.** 백엔드 없이 예시 데이터(`frontend/src/api/mock/`)로 모든 흐름이 동작 |
| 백엔드 (`backend/`) | 뼈대 + 채팅 정책(분류 → 정책 → 프롬프트) 로직과 테스트. API는 `/api/health`만 |
| NLP (`nlp/`) | 분류기 자리만 있음(항상 "모호함"). 누출 판별 · AI 작성 점수는 계약 제안 단계 |
| 문서 | 화면 명세 · API 계약을 v3 기준으로 갱신(결정 필요 항목 남음). 스키마 · 채팅 정책 · 연동 계약은 각 담당이 v3에 맞춰 갱신 예정 |

## 처음 보는 팀원을 위한 안내

### 화면 둘러보기 (백엔드 없이 5분)
```bash
cd frontend
npm install
npm run dev
```
http://localhost:5173 을 열고 아래 순서로 눌러 본다. 화면 위 "예시 데이터로 보는 중" 칩은 아직 백엔드에 안 붙었다는 표시다.
1. **교수자** (`/teacher/classes`) — "프로그래밍 기초 1분반" → 과제 카드의 리포트 · 채점 · 결과 공개, "학생 관리", "새 과제 만들기"(샘플 과제로 시작 → 4단계 → 학생처럼 졸라보기 → 배포)
2. **학생** (`/student/classes`) — "3주차 과제" 풀기 → 오른쪽 AI에게 "코드 전체 짜주세요" → 도움 방식 고르기 → 문항 제출(개념 확인) → 다섯 문항 다 내고 최종 제출 → 이해 확인
3. 다시 교수자 클래스 화면에서 **결과 공개** → 학생 "내 리포트"
- 위 화면 이동은 메뉴로 한다. 브라우저를 새로고침하면 예시 데이터가 처음 상태로 돌아간다.
- 학생 입장 시험: `/student/join`에서 수업 코드 `TG-4821` + 아무 수업용 ID → 참여 요청 → 교수자 "학생 관리"에서 수락
- 교수자 로그인 시험: 아무 이메일 + 4자 이상 비밀번호
- 학생 화면의 "판별 과정 표시 (시연용)"를 켜면 요청 분류 → 시도 근거 → 누출 검사 과정이 보인다.

### 어디를 보면 되나
| 알고 싶은 것 | 볼 곳 |
|---|---|
| 어떤 화면이 있고 각각 뭘 하나 | [docs/planning/screens.md](docs/planning/screens.md) |
| 화면과 서버가 주고받는 API | [docs/spec/api-contract.md](docs/spec/api-contract.md) |
| 서버와 NLP 모델 사이 약속 | [docs/spec/integration-contract.md](docs/spec/integration-contract.md) |
| DB 테이블 | [docs/planning/schema.md](docs/planning/schema.md) |
| AI가 어떤 기준으로 답하나 | [docs/spec/chat-policy.md](docs/spec/chat-policy.md) |
| 일정 | [docs/planning/milestones.md](docs/planning/milestones.md) |
| 코드 규칙 · 브랜치 · PR | [docs/conventions/](docs/README.md) |

### 프론트 코드 구조 한눈에
```
frontend/src/
├── pages/teacher/   교수자 화면 (editor/ 과제 만들기, report/ 반 리포트, grading/ 채점, students/ 학생 관리 …)
├── pages/student/   학생 화면 (solve/ 과제 풀이, check/ 이해 확인 …)
├── components/      여러 화면이 같이 쓰는 조각 (코드 블록, 답 입력, 테스트 결과 …)
├── hooks/           제출 · 채팅 · 붙여넣기 기록 로직
├── api/             서버 호출 함수와 데이터 타입 ← 백엔드가 생기면 여기만 바꾼다
│   └── mock/        지금 쓰는 예시 데이터 (백엔드 연결 후 삭제)
└── styles/          색 · 폰트 · 공통 클래스
```
**백엔드를 붙이는 방법:** 예를 들어 `api/classes.ts`의 `listClasses = () => mockClasses.list()`를 `() => api<ClassInfo[]>('/classes')`처럼 바꾸면 화면은 그대로 실제 데이터를 쓴다. 주소와 데이터 모양은 [API 계약](docs/spec/api-contract.md)에 함수별로 적혀 있다.

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
- 확인: http://localhost:5173 → 시작 화면의 초록색 "백엔드 연결됨" 칩이 보이면 백엔드까지 정상. 백엔드가 꺼져 있어도 화면은 예시 데이터로 동작한다.
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
