# 마일스톤

> 상태: **초안** — 팀 확인 필요. 범위가 바뀌면 [scope.md](scope.md)와 이 문서부터 고친다.
> 최종 목표: 12/1(화) 시연 가능한 프로토타입(프로그래밍 과제만, 시연 과제는 **C**). 실서비스 수준의 결제·보안·확장성은 범위 밖.
> 일정(11/21 변경): **11/25(수)까지 개발 완료 — 실제 모델 연결까지.** 11/26–11/30은 부족한 부분 보완, 12/1 시연.
> 체크 표시: `[x]` 코드·문서 완료(PR 번호, 머지 전이면 "리뷰 대기") / `[ ]` 남음. 담당: **[백엔드]** **[프론트]** **[NLP]** **[공통]**

## 시연 시나리오 (11/25까지 끝까지 동작해야 하는 경로)
1. 교수자 로그인 → 클래스 개설(요금제·시작 날짜) → 학생 명단 넣기
2. 과제 만들기: **md 과제 파일 올리기 → 문항 추출 확인** → AI 도움 설정 → 학생처럼 졸라보기 → 배포
3. 학생: 수업 코드 + 학번으로 입장 → 기록 동의 → 과제 풀기
4. 학생이 AI에게 "코드 전체 짜주세요" → **실제 분류기 + 실제 LLM(Ollama + Qwen)** → 도움 방식 고르기 → 힌트만
5. C 코드 작성 → 공개 테스트 실행(Docker) → 문항 제출 → 개념 확인 → 최종 제출 → 이해 확인
6. 교수자: 결과 공개 · 반 리포트 · 간단 제작 채점 → 학생: 내 리포트

> 우선순위: 위 경로에 필요한 것부터. 경로 밖 기능(결제 목업, 학생별 기록 등)은 11/25에 못 끝나면 11/26–11/30으로 미룬다.

---

## M1 · 11/17 — 설계 ✅
- [x] 화면 시안 v3 — [page_design.html](page_design.html)
- [x] 화면별 기능 명세 — [screens.md](screens.md) (프론트 전체 화면 구현, 예시 데이터)
- [x] DB 스키마 v3 — [schema.md](schema.md) (PR #6)
- [x] API 계약 v3 — [../spec/api-contract.md](../spec/api-contract.md) (PR #6)
- [x] 개발 범위 — [scope.md](scope.md) (PR #4)
- [x] 코드 뼈대 · 채팅 정책 로직(분류 → 정책 → 프롬프트) — PR #1
- [x] Docker 코드 실행기(Python) — PR #3

---

## M2 · 11/25(수) — 개발 완료 + 모델 연결

### 백엔드 기반
- [x] **[백엔드]** KST 시각 · `KstDateTime` · 비밀번호 해시 · Enum · 요금제 · `AiPolicy` — PR #7 (리뷰 대기)
- [x] **[백엔드]** 테이블 5개(users · classes · class_payments · enrollments · class_members), PK `seq`, 시드 — PR #8 (리뷰 대기)
- [ ] **[백엔드]** ② 인증 — `feature/auth` (설계·계획 완료, 구현 전)
  - [ ] 에러 형식 `{code, message, trace_id}` + `X-Request-Id`
  - [ ] JWT(`JWT_SECRET` 32자 이상) · 교수자 토큰 12시간
  - [ ] `POST /auth/signup` · `POST /auth/login`
  - [ ] 권한 의존성(교수자만 · 학생만, 역할은 DB 기준)

### 백엔드 API (시연 경로 순서)
- [ ] **[백엔드]** ③ 클래스 · 참여 — `feature/class-api`
  - [ ] 클래스 개설(요금제 상한 복사, 수업 코드 발급·중복 시 재발급, 시작 날짜 → `starts_at`, 만료 = +1년) · 목록 · 상세
  - [ ] 클래스 AI 기본값 조회·저장(`/ai-defaults`)
  - [ ] 명단 · 입장 방식 조회·저장(`is_use` 토글, 저장 시 대기 중 요청 자동 수락)
  - [ ] **학생 입장** `POST /enrollments`: 수업 코드 + 학번 → 학생 계정 · 학생 토큰(클래스 만료까지). `CLASS_NOT_STARTED` · `CLASS_FULL` · `CLASS_EXPIRED` · 내보낸 학번 `FORBIDDEN`
  - [ ] 참여 상태 확인 · 기록 동의 · 참여 요청 목록 · 수락·거절 · 학생 내보내기 · 학생 목록 · `/me/classes`
  - [ ] 권한 테스트(I7): 남의 클래스 · 다른 학생 데이터 접근 → `FORBIDDEN`
- [ ] **[백엔드]** ⑤ 프롬프트 조립 — `feature/prompt-builder`
  - [ ] `ResponseMode` 대문자 + `OFFER_CHOICES`
  - [ ] `build_from_config`: 고정 규칙 → 정책 지시 → 교수자 지시 → `<과제 설명>` → `<알려 주면 안 되는 값>` ([chat-policy.md](../spec/chat-policy.md))
  - [ ] 인젝션 테스트(과제 설명 · 학생 메시지에 지시 심기 → 고정 규칙 유지)
- [ ] **[백엔드]** C 실행기 — `feature/c-runner`
  - [ ] gcc 실행 이미지(격리 옵션 동일: 네트워크 없음 · 메모리 · 시간 · 비root)
  - [ ] 테스트 모양 `{input, expected_output}`(표준 입력 → 표준 출력), 컴파일 오류 안내
  - [ ] 실행기 테스트 이미지 확인 `:latest` 수정(지금 Docker 테스트 4개가 건너뛰어짐)
- [ ] **[백엔드]** ④ 과제 · 문항 — `feature/assignment-api`
  - [ ] `assignments` · `questions` 모델(`answer_key` 분리, `public_tests`)
  - [ ] **md 과제 추출** `POST /classes/{id}/assignments/extract` — 정해진 양식(샘플 `docs/spec/samples/c-binary-assignment.md`, md 추출 PR에서 테스트 자료로 추가), 규칙(정규식)으로 파싱, 양식 오류 안내
  - [ ] 초안(샘플·빈 과제) · 저장 · 조회 · 배포 · 결과 공개 · 정책 미리보기 · 지시문 초안
  - [ ] 학생처럼 졸라보기(`/assignments/simulate`) — 실제 정책 경로로 우회 요청 실행
  - [ ] 학생용 조회에 `answer_key` 값이 하나도 없는지 테스트
  - [ ] 시드에 C 과제(2진수 변환기·덧셈기·뺄셈기) 추가
- [ ] **[백엔드]** ⑦ 풀이 · 제출 — `feature/submission-api`
  - [ ] `submissions` · `answers` 모델, 학생 과제 조회 · 내 제출
  - [ ] 공개 테스트 실행 `/run`(C 실행기)
  - [ ] 문항 제출(다시 제출 · 제출 횟수) · 자동 채점(객관식 · 출력 예측 · 코드 숨김 테스트)
  - [ ] 개념 확인(질문 1개 + AI 작성 신호 높으면 1개 더) · 답 고치러 돌아가기
  - [ ] 최종 제출(마감 뒤 불가, 안 낸 문항 있으면 `CONFLICT`)
  - [ ] 결과 공개 전 정오·점수·숨김 테스트 결과를 학생 응답에서 빼는 테스트
- [ ] **[백엔드]** ⑥ 채팅 — `feature/chat-api`
  - [ ] `chat_messages` 모델, 문항별 대화 조회 · 보내기
  - [ ] 사용량 상한(I6: 상한이면 LLM 호출 없이 `USAGE_LIMIT`)
  - [ ] 도움 방식 고르기(`OFFER_CHOICES` → `FIRST_HINT` · `FEEDBACK` · `ORIGINAL`, 정책은 `HINT_ONLY` 유지 — I1)
  - [ ] 잠김: 개념 확인 중 · 최종 제출 후 · AI 끈 간단 제작 문항
  - [ ] LLM에는 최근 대화 N개만, 분류 결과·누출 검사 결과 저장
- [ ] **[백엔드]** 붙여넣기 기록 `POST /paste-events`(길이·시점만, 내용 필드 거부 — I5)
- [ ] **[백엔드]** 이해 확인 · 내 리포트 · 교수자 반 리포트 · 간단 제작 채점 · 학생별 기록
- [ ] **[백엔드]** 요금제 · 결제 목업 `/plans` · `/payments`(실제 PG 연동 없음, 항상 성공)

### 모델 연결 (11/25까지)
- [ ] **[NLP]** Qwen 버전·크기 확정(7B~8B 권장), 시연 PC에서 `ollama pull` · 응답 속도 측정
- [ ] **[백엔드]** Ollama Provider 점검 — Qwen 3이면 thinking 끄기, 타임아웃, `LLM_PROVIDER=ollama`로 채팅 경로 확인
- [ ] **[NLP]** 분류기 `classify()` 구현 — 계약 [integration-contract.md](../spec/integration-contract.md) (`is_learning_context` · `requests_complete_answer` · `has_self_attempt_evidence` · `uncertain` · `confidence`)
- [ ] **[백엔드]** 분류기 교체 확인 — `CLASSIFIER=module` 또는 `http`, 계약 테스트, 모호하면 되묻기(I2)
- [ ] **[NLP]** AI 답변 누출 검사(정답·완성 코드 판별) 구현
- [ ] **[백엔드]** 누출 검사 연결 — 막히면 초안 대신 안전한 응답, `leak_check` 저장
- [ ] **[NLP]** 개념 확인 답변 "AI 작성 점수" 담당·포함 여부 확정(scope.md ②), 하면 구현
- [ ] **[공통]** 실제 모델로 시연 시나리오 4번(정답 요청 → 힌트만) 통과 확인

### 프론트 연결
- [ ] **[프론트]** `client.ts`: 토큰 저장 · `Authorization: Bearer` · 에러 `{code, message}`로 분기
- [ ] **[프론트]** 타입 변경: id → `seq: number`, `alias` → `student_no`, 명단 `{student_no, is_use}[]`, 클래스 개설 `starts_on`, `AiPolicy.usage_limit`, 개념 확인·채팅 요청 `pasted` 제거
- [ ] **[프론트]** 클래스 개설 화면에 시작 날짜 선택
- [ ] **[프론트]** 과제 파일 올리기: `.md`만 받고 실제 파일 전송(`multipart`)
- [ ] **[프론트]** 백엔드 API가 생기는 순서대로 `api/<도메인>.ts`의 mock → 실제 호출 교체, 교체한 mock 코드 삭제
  - [ ] 인증 · 클래스 · 참여 · 명단
  - [ ] 과제 만들기 · 추출 · 배포
  - [ ] 풀이 · 제출 · 테스트 실행 · 개념 확인 · 이해 확인
  - [ ] 채팅 · 붙여넣기
  - [ ] 리포트 · 채점 · 결과 공개 · 결제

### 문서
- [ ] **[백엔드]** md 과제 양식 문서(`docs/spec/`, scope.md ③) — 샘플 md를 기준으로
- [ ] **[공통]** 결정 필요: `AiPolicy` CUSTOM인데 지시문 비어 있음 허용 여부 · 지시문 최대 길이 (PR #7)

---

## M3 · 11/26(목)–11/30(월) — 보완
- [ ] **[공통]** 11/25 기준 시연 시나리오 전체를 돌려 보고 막힌 곳 목록 만들기
- [ ] **[공통]** 우회 시도 검증(별도 세션): "학생이 정답을 받아낼 방법" · "다른 학생 데이터를 볼 방법" → 찾은 사례는 테스트로 먼저 고정 후 수정
- [ ] **[공통]** 보안 점검: 역할 권한 · 남의 클래스 접근 · 입력 검증 · 비밀값 노출(`.env`, 로그)
- [ ] **[NLP]** 실제 대화로 분류기 · 누출 검사 정확도 점검, 기준값(`CLASSIFIER_MIN_CONFIDENCE`) 조정
- [ ] **[백엔드]** Qwen 응답 품질에 맞춰 프롬프트 문구 조정(정답 금지 · 시도 지어내기 금지가 지켜지는지)
- [ ] **[백엔드]** 미룬 작은 지적 정리(PR #7 · #8 본문)
- [ ] **[백엔드]** (여유 있으면) PDF 과제 추출 — 같은 양식, 텍스트 변환 단계만 추가
- [ ] **[프론트]** 화면 다듬기 · 오류 문구 · 로딩 상태, 남은 mock 제거
- [ ] **[공통]** 시연 PC 준비: Docker · 실행 이미지 빌드, Ollama 모델 받기, `backend/.env`(`JWT_SECRET`, `LLM_PROVIDER=ollama`, `CLASSIFIER`), 시드
- [ ] **[공통]** README 최종 정리 · 시연 대본 · 리허설 2회 이상

## 12/1(화) — 시연
- [ ] 시연 직전 확인: 서버 2개(백엔드 · 프론트) · Ollama · Docker 실행 중, 시드 새로 넣기
- [ ] 비상 대책: LLM이 느리거나 안 되면 `LLM_PROVIDER=mock`, 분류기가 안 되면 `CLASSIFIER=stub`, Docker가 안 되면 `CODE_RUNNER=mock`

---

## 위험 요소
- **일정이 짧다(11/21–11/25, 5일)** → 시연 경로 기능부터 하고, 경로 밖 기능은 11/26 이후로 미룬다. 백엔드 API가 나오는 대로 프론트가 바로 붙여 끝에 몰리지 않게 한다.
- 로컬 LLM 속도·한국어 품질 → 11/23까지 시연 PC에서 Qwen 응답 속도를 먼저 잰다.
- Qwen 3 계열은 답 전에 생각 과정(thinking)을 출력해 정답이 섞일 수 있다 → 호출할 때 끈다.
- C 실행 이미지·테스트 모양이 아직 없다 → 과제·제출 API보다 먼저 만든다.
- 시연 PC에 Docker가 없으면 코드 실행이 안 된다 → `CODE_RUNNER=mock`으로 대체할 수 있게 유지한다.
- NLP 모델이 늦어질 경우 → 키워드 스텁으로 시연할 수 있게 유지한다.
