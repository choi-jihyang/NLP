# 코드 컨벤션

> 단일 출처. 규칙 = **반드시 지킨다**. 권장 = 지키되 합리적 예외 허용.
> 자동 검사: frontend `npm run lint`(oxlint) + `npm run build`(tsc 타입 검사), backend `ruff check`.
> 줄 수 상한처럼 도구가 아직 검사하지 않는 항목은 리뷰에서 확인한다.

---

## 목차
1. [모노레포 경계](#1-모노레포-경계)
2. [프론트엔드 — 폴더](#2-프론트엔드--폴더)
3. [프론트엔드 — 화면 / 컴포넌트 / 훅](#3-프론트엔드--화면--컴포넌트--훅)
4. [프론트엔드 — 타입 · 스타일](#4-프론트엔드--타입--스타일)
5. [백엔드 — 계층](#5-백엔드--계층)
6. [백엔드 — 교체 가능한 연동(LLM · 분류기)](#6-백엔드--교체-가능한-연동llm--분류기)
7. [백엔드 — 타입 · 비동기](#7-백엔드--타입--비동기)
8. [네이밍](#8-네이밍)
9. [Import 순서](#9-import-순서)
10. [파일 길이](#10-파일-길이)

---

## 1. 모노레포 경계
```
NLP/
├── frontend/   React + TypeScript (Vite)
├── backend/    Python FastAPI
├── nlp/        NLP 팀 분류기 (thinkguard_nlp 패키지 + HTTP 서버)
└── docs/       conventions / planning / spec
```
- **규칙**: `frontend`는 백엔드를 **HTTP API로만** 호출한다. 백엔드 코드를 import하지 않는다.
- **규칙**: `backend`는 `nlp`를 **분류기 계약을 통해서만** 쓴다(`CLASSIFIER=module` 또는 `http`). `nlp` 내부 함수를 직접 import하지 않는다. → [../spec/integration-contract.md](../spec/integration-contract.md)
- **규칙**: `nlp`는 `backend`를 import하지 않는다. 주고받는 데이터는 dict(JSON)뿐이다.

---

## 2. 프론트엔드 — 폴더
```
frontend/src/
├── pages/              # 라우트 단위 화면 (App.tsx의 Route 하나 = 파일 하나)
│   ├── auth/           # 로그인, 회원가입
│   ├── teacher/        # 교수자 화면
│   └── student/        # 학생 화면
├── components/         # 여러 화면이 함께 쓰는 UI
│   └── layout/         # 헤더·탭 레이아웃
├── hooks/              # 화면 로직 훅 (useSubmission, useChat, usePasteLog …)
├── api/                # 백엔드 호출 함수 + 요청/응답 타입
│   ├── client.ts       # fetch 공통 함수 (유일한 fetch 위치)
│   └── mock/           # 백엔드가 생기기 전까지 쓰는 예시 데이터 (화면은 직접 import 금지)
└── styles/
    ├── tokens.css      # 디자인 토큰 (색·폰트 단일 출처)
    ├── base.css        # 공통 클래스 (.panel, .btn, .chip …)
    ├── components.css  # 여러 화면이 쓰는 위젯 (코드 블록, 테스트 결과, 선택지, 표 …)
    └── screens.css     # 화면 전용 배치 (과제 풀이, 과제 만들기, 리포트)
```
- **규칙**: `fetch()`는 `api/client.ts`에서만 호출한다. 다른 파일은 `api/`의 함수를 쓴다.
- **규칙**: 새 API를 붙이면 `api/<도메인>.ts`에 함수와 응답 타입을 함께 둔다(예: `api/classes.ts`).
- **규칙**: 예시 데이터(`api/mock/`)는 `api/<도메인>.ts`의 함수만 부른다. 화면·컴포넌트·훅은 `api/mock/`을 직접 import하지 않는다. 백엔드 API가 생기면 함수 안쪽만 `client.ts` 호출로 바꾸고 해당 mock 코드를 지운다.
- **권장**: 한 화면에서만 쓰는 컴포넌트가 늘어나면 `pages/<영역>/<화면>/` 폴더로 묶는다.

---

## 3. 프론트엔드 — 화면 / 컴포넌트 / 훅

| 파일 유형 | 위치 | 역할 | 금지 |
|---|---|---|---|
| **Page** | `pages/` | 라우트 진입점. 훅·컴포넌트 조합, 배치 | `fetch` 직접 호출 |
| **Component** | `components/` 또는 화면 폴더 | 표현 단위. props로 렌더링 | `fetch` 직접 호출, 서버 상태 보관 |
| **Hook** | `hooks/` | 상태 + 화면 로직 | JSX 반환 |

- **규칙**: 서버 데이터는 **TanStack Query**(`useQuery`/`useMutation`)로 다루고, `queryFn`·`mutationFn`에는 `api/` 함수를 넘긴다.
- **규칙**: 1 파일 = 1 컴포넌트(default export 또는 이름 있는 export 1개). Props 타입을 파일 안에 선언한다.
- **규칙**: Hook 이름은 `use`로 시작한다. `useEffect` 의존성 배열을 빠짐없이 적는다.
- **권장**: 컴포넌트 안에 `useState`와 로직이 섞여 길어지면 훅으로 뺀다(예: `useChat`, `usePasteLog`).

```tsx
// ✅ Page는 api 함수를 Query에 넘기기만
const health = useQuery({ queryKey: ['health'], queryFn: getHealth })

// ❌ Page에서 직접 fetch
useEffect(() => { fetch('/api/health').then(...) }, [])
```

---

## 4. 프론트엔드 — 타입 · 스타일
- **규칙**: `any` 금지. 모르는 값은 `unknown`으로 받고 좁혀서 쓴다.
- **규칙**: API 응답 타입은 백엔드 Pydantic 스키마와 **필드 이름을 그대로** 맞춘다(snake_case 유지, 변환 계층 없음).
- **규칙**: 색·폰트는 `styles/tokens.css`의 CSS 변수(`var(--accent)` 등)만 쓴다. 색 코드를 직접 적지 않는다.
- **규칙**: UI 문구는 한국어로 쓴다.
- **권장**: 공통 클래스(`.panel`, `.btn`, `.chip`…)를 먼저 쓰고, 화면 전용 스타일이 필요할 때만 CSS를 추가한다.

---

## 5. 백엔드 — 계층
```
backend/app/
├── main.py             # FastAPI 앱 생성, 미들웨어, 라우터 등록
├── core/               # 설정(config.py), 인증(JWT)·권한 의존성
├── db/                 # 엔진·세션·Base
├── models/             # SQLAlchemy ORM 모델 (테이블 하나 = 클래스 하나)
├── schemas/            # Pydantic 요청/응답 모델
├── api/routes/         # 기능별 라우터 (auth, classes, chat, …)
├── services/           # 비즈니스 로직
├── llm/                # LLM Provider 인터페이스 + 구현
└── classifier/         # 분류기 인터페이스 + 구현
```

```
api/routes  →  services  →  models · llm · classifier
(HTTP 변환)    (로직 본체)    (데이터 · 외부 연동)
```

| 계층 | 역할 | 금지 |
|---|---|---|
| `api/routes` | 요청 검증(Pydantic) → service 호출 → 응답 변환 | 비즈니스 로직, 프롬프트 조립 |
| `services` | 로직 본체. 테스트 대상의 중심 | `fastapi` import(Request·HTTPException 등), 구체 Provider 직접 생성 |
| `models` | 테이블 정의 | 비즈니스 로직 |

- **규칙**: 라우터는 얇게. 한 엔드포인트 함수가 20줄을 넘으면 로직을 service로 옮긴다.
- **규칙**: service는 FastAPI 없이 테스트할 수 있어야 한다. DB 세션·Provider·분류기는 **인자로 받는다**.
- **규칙**: 에러는 [../spec/error-handling.md](../spec/error-handling.md)의 형식으로 응답한다.
- **권장**: service 하나가 모델 5개 이상을 다루면 분리를 검토한다.

---

## 6. 백엔드 — 교체 가능한 연동(LLM · 분류기)
- **규칙**: service는 `LLMProvider`·`Classifier` **인터페이스에만** 의존한다. `OllamaProvider()`처럼 구현을 직접 만들지 않는다.
- **규칙**: 구현 선택은 `get_llm_provider()`·`get_classifier()`가 환경변수로만 한다. `if provider == "ollama"` 분기를 다른 곳에 쓰지 않는다.
- **규칙**: 새 구현(예: 다른 LLM)은 `llm/<이름>.py`에 인터페이스를 구현하고, 팩토리에 한 줄 추가한다.

---

## 7. 백엔드 — 타입 · 비동기
- **규칙**: 함수 인자·반환에 타입 힌트를 단다.
- **규칙**: 외부 호출(LLM, 분류기 HTTP)은 `async` + `httpx.AsyncClient`. 동기 라이브러리는 `anyio.to_thread`로 감싼다.
- **규칙**: 설정은 `core/config.py`의 `get_settings()`로만 읽는다. `os.environ`을 직접 읽지 않는다.

---

## 8. 네이밍
| 대상 | 규칙 | 예시 |
|---|---|---|
| React 컴포넌트·Page 파일 | PascalCase | `SolvePage.tsx`, `ChatPanel.tsx` |
| Hook | `use` + camelCase | `useChat.ts` |
| TS 함수·변수 | camelCase | `getHealth`, `inviteCode` |
| TS 타입 | PascalCase | `Health`, `ChatTurn` |
| TS·Python 상수 | UPPER_SNAKE_CASE | `TEACHER_NAV`, `FIXED_RULES` |
| TS 일반 파일 | camelCase | `client.ts` |
| Python 모듈·함수·변수 | snake_case | `prompt_builder.py`, `build_from_config` |
| Python 클래스 | PascalCase | `KeywordStubClassifier` |
| API 경로 | kebab-case 복수형 | `/api/classes/{class_id}/ai-settings` |
| DB 테이블·컬럼 | snake_case 복수형 테이블 | `paste_events.pasted_at` |

---

## 9. Import 순서
- **TypeScript**: ① 외부 라이브러리(react, react-router-dom…) ② 프로젝트 내부(`../api`, `../components`) ③ 같은 폴더(`./`) ④ CSS. 그룹 사이에 빈 줄.
- **Python**: ruff(`I` 규칙)가 자동 정렬한다 — `ruff check --fix`.

---

## 10. 파일 길이
| 기준 | 상한 |
|---|---|
| 파일 전체 | **200줄** (테스트 파일 제외) |

초과하면: Page → 컴포넌트 추출 / 컴포넌트 → 하위 컴포넌트 / 훅 → 관심사별 분리 / service → 유스케이스별 분리.
