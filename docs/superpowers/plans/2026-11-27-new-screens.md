# v4 새 화면 적용 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/planning/design/` 시안(PR #20)대로 프론트 화면 · 흐름을 바꾸고, 다크모드와 교수자 · 학생 마이페이지를 더한다. 백엔드는 바꾸지 않는다.

**Architecture:** 색 · 공통 클래스는 CSS에서 먼저 바꿔(기존 클래스 이름 `.btn` `.panel` `.chip` 유지) 손대지 않은 화면도 새 모양이 되게 한다. 그 위에 공통 조각(로고 · 헤더 · 화면 머리 · 클래스 머리 탭)을 만들고, 흐름이 바뀐 화면(메인 · 로그인 · 내 클래스 · 요금제 · 클래스 개설 · 입장 · 내 과제 · 마이페이지)만 화면 구조를 다시 짠다. 데이터는 지금 `api/` 함수 그대로 쓴다.

**Tech Stack:** React 19 + TypeScript + Vite, TanStack Query, react-router-dom 7, CSS(디자인 토큰), oxlint.

**Spec:** `docs/planning/screens.md` "v4 변경점" · `docs/spec/api-contract.md` "마이페이지 (v4 · 새 API 없음)" · 시안 `docs/planning/design/main_page_design.html`, `docs/planning/design/mockup/*.html`(공통 스타일 `mockup/common.css`).

## Global Constraints
- **새 백엔드 작업 없음.** 새 API · 테이블을 만들지 않는다. 결제 화면 · 결제 단계 없음. 결제 내역은 예시 데이터, 이름 수정 · 비밀번호 변경 · 1년 연장은 화면만(저장 안 함). 계정 만들기는 지금 `signup` 호출을 그대로 연결.
- "결제하고 개설"은 안에서 `payMock({plan, kind:'NEW'})` → `createClass(...)` 후 `/teacher/classes/:id`로 이동.
- `fetch()`는 `api/client.ts`에서만. 예시 데이터는 `api/<도메인>.ts` 함수만 부르고 화면은 `api/mock/`을 직접 import하지 않는다.
- 색 · 폰트는 `styles/tokens.css` 변수만. 색 코드를 다른 파일에 직접 쓰지 않는다(로고 SVG는 `var(--logo)` 등 변수 사용).
- 파일 하나 200줄 이하(CSS 포함). UI 문구는 한국어. `any` 금지. 1 파일 = 1 컴포넌트.
- 다크모드: `html[data-theme="dark"]`. 처음엔 `prefers-color-scheme`, 고른 값은 `localStorage` 키 `tg-theme`. 다크 색은 무채색(`--bg:#111214; --surface:#18191c; --surface-2:#212226; --line:#2c2e33` …, 시안 `common.css` 다크 블록 그대로).
- 불변식 I5(붙여넣기 내용 저장 안 함) · I8(학생 응답에 정답 없음)을 건드리지 않는다: 풀이 · 채팅 · 붙여넣기 훅(`useChat`, `usePasteLog`, `useSubmission`)의 동작은 바꾸지 않고 화면 모양만 바꾼다.
- 아직 올리지 않은 버그 수정(develop 작업 폴더의 `ClassStudentsPage.tsx` · `StudentList.tsx`, `?assignment=a1` → 실제 과제 번호)과 충돌을 줄이기 위해 두 파일은 **JSX 구조를 바꾸지 않고** 감싸는 머리만 더한다.
- **커밋 · push · PR은 사용자 승인 뒤에만.** 각 작업의 Commit 단계에서는 커밋 메시지(`[new-screens] 제목` + `*` 줄, commit-convention.md)와 파일 목록을 먼저 보여 주고 승인받는다.
- 검사: `cd frontend && npm run build && npm run lint` 통과. 프론트에는 테스트 도구가 없으므로(새 의존성 추가 안 함) 각 작업은 빌드 · 린트 + 브라우저 확인으로 검증한다.

## Review Focus
- **새로 고침 뒤 헤더 이름**: 교수자가 탭을 새로 고쳐도 헤더 · 마이페이지 이름이 비지 않아야 한다(로그인 응답 `user`를 sessionStorage에 저장 · 없으면 "교수자"로 표시). → Task 3
- **다크모드에서 읽히지 않는 글자**: `.pill.primary`처럼 `--fg` 배경을 쓰는 곳은 글자를 `var(--bg)`로. 코드 블록 · 교수자 띠가 다크 배경과 구분돼야 한다. → Task 1 확인 단계
- **결제하고 개설 두 번 누르기**: 진행 중엔 버튼을 막아 이용권이 두 장 생기지 않게. 실패하면 메시지를 보이고 화면에 머문다. → Task 9
- **좁은 화면(375px)**: 헤더 오른쪽 메뉴 · 숫자 4칸 · 풀이 2단이 가로 스크롤 없이 접혀야 한다. → 각 작업 확인 단계 + Task 15
- **시작 전 · 빈 상태**: 과제 없는 클래스, 클래스 없는 교수자, 참여한 클래스 없는 학생에서 "지금 할 일" · 카드가 빈 문구를 보여야 한다(오류 아님). → Task 7, 13

---

## File Structure
| 파일 | 역할 |
|---|---|
| `frontend/index.html` | 폰트 굵기 600 추가, 첫 그림 전 테마 적용 인라인 스크립트 |
| `src/styles/tokens.css` | 라이트 · 다크 토큰 (시안 값) |
| `src/styles/base.css` | 공통 클래스(.btn=알약, .panel, .chip, 폼) 시안 모양으로 |
| `src/styles/layout.css` (새) | `.nav` 헤더 · `.head` 화면 머리 · `.subtabs` · `.theme-btn` |
| `src/styles/home.css`, `home-demo.css` (새) | 메인 스크롤 화면 |
| `src/styles/pages.css` (새) | 대시보드 · 카드 · 마이페이지 · 입장 · 내 과제 흐름 막대 |
| `src/hooks/useTheme.ts` (새) | 테마 읽기 · 바꾸기 |
| `src/components/layout/Logo.tsx` (새) | 방패 로고 |
| `src/components/layout/ThemeToggle.tsx` (새) | 해/달 버튼 |
| `src/components/layout/AppLayout.tsx` | 새 헤더(역할별 메뉴 · 오른쪽 링크) |
| `src/components/PageHead.tsx` (새) | 그래프 용지 머리(라벨 · 제목 · 설명 · 버튼) |
| `src/components/CopyCode.tsx` (새) | 수업 코드 + 복사 |
| `src/api/client.ts`, `src/api/auth.ts` | 로그인 사용자(이름 · 이메일) 탭 저장 |
| `src/api/payments.ts` (새) | 결제 내역 예시 데이터 함수 |
| `src/pages/HomePage.tsx` + `pages/home/*` (새) | 메인 스크롤 |
| `src/pages/auth/AuthPage.tsx` (새) | 로그인 / 계정 만들기 탭 (Login · Signup 폼 재사용) |
| `src/pages/teacher/ClassListPage.tsx` + `teacher/overview/*` (새) | 대시보드 |
| `src/hooks/useTeacherOverview.ts` (새) | 대시보드 숫자 · 할 일 모으기 |
| `src/pages/teacher/PlansPage.tsx`, `ClassCreatePage.tsx` | 요금제 카드 · 결제하고 개설 |
| `src/pages/teacher/ClassHeader.tsx` (새) | 클래스 머리 + 탭(과제 · 학생 · AI 기본값) |
| `src/pages/teacher/mypage/*` (새) | 교수자 마이페이지 |
| `src/pages/student/JoinClassPage.tsx` | 입장 → 동의 → 대기 한 화면 |
| `src/pages/student/StudentClassPage.tsx` + `student/TaskCard.tsx` (새) | 내 과제 카드 · 흐름 막대 |
| `src/pages/student/StudentMyPage.tsx` (새) | 학생 마이페이지 |
| `src/App.tsx` | 경로 추가(`/teacher/mypage`, `/student/mypage`), `/login` · `/signup` → AuthPage |

---

### Task 1: 토큰 · 다크모드 · 공통 클래스

**Files:**
- Modify: `frontend/index.html`, `src/styles/tokens.css`, `src/styles/base.css`, `src/styles/components.css`(색 코드 · 반경만)
- Create: `src/styles/layout.css`, `src/hooks/useTheme.ts`, `src/components/layout/ThemeToggle.tsx`
- Modify: `src/main.tsx`(layout.css import)

**Interfaces:**
- Produces: `useTheme(): { theme: 'light' | 'dark'; toggle: () => void }`, `<ThemeToggle />`, CSS 클래스 `.nav .nav-in .logo .menu .nav-right .who .avatar .theme-btn .head .head-row .eyebrow .sub .subtabs`, `.btn`(알약 모양) `.btn.primary` `.btn.ghost` `.btn.text` `.btn.sm`

- [ ] **Step 1: tokens.css를 시안 값으로 바꾼다.** `:root`는 시안 `mockup/common.css` 2–13행 값(--code-bg `#16181b`, --code-fg `#e8e9eb`, --r `16px`)에 기존 `--scrim` · `--shadow-sm`을 유지한다. 다크는 시안 `common.css` 205–212행 블록을 `html[data-theme="dark"]`로 옮긴다. `--scrim`은 다크에서 `rgba(17,18,20,.88)`, `--nav-bg`를 새로 두어 라이트 `rgba(250,252,251,.85)` / 다크 `rgba(17,18,20,.85)`.

- [ ] **Step 2: index.html** 폰트 URL을 `Hahmlet:wght@500;600;700`로 바꾸고, `<head>` 끝에 첫 그림 전 테마를 정하는 스크립트를 넣는다.
```html
<script>
  try {
    var t = localStorage.getItem('tg-theme')
    var dark = t ? t === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  } catch (e) { document.documentElement.setAttribute('data-theme', 'light') }
</script>
```

- [ ] **Step 3: useTheme 훅**
```ts
// src/hooks/useTheme.ts
import { useCallback, useState } from 'react'

export type Theme = 'light' | 'dark'
const KEY = 'tg-theme'
const current = (): Theme => (document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light')

/** 라이트 · 다크 전환. 고른 값은 이 브라우저에 기억한다(index.html이 첫 그림 전에 적용) */
export function useTheme(): { theme: Theme; toggle: () => void } {
  const [theme, setTheme] = useState<Theme>(current)
  const toggle = useCallback(() => {
    const next: Theme = current() === 'dark' ? 'light' : 'dark'
    document.documentElement.setAttribute('data-theme', next)
    try { localStorage.setItem(KEY, next) } catch { /* 저장 못 해도 이번 화면은 바뀐다 */ }
    setTheme(next)
  }, [])
  return { theme, toggle }
}
```

- [ ] **Step 4: ThemeToggle** — `button.theme-btn`, `aria-label`·`title`은 다크면 "밝은 화면으로", 아니면 "어두운 화면으로". 아이콘은 시안 `theme.js`의 SUN · MOON SVG(`stroke="currentColor"`).

- [ ] **Step 5: base.css** — 시안 `common.css`의 `body` · `h1–h3` · `.wrap`(1180px) · `.mono` · `.muted` · `.eyebrow`를 옮기고, `.btn`을 시안 `.pill` 모양으로 바꾼다(`border-radius:99px; padding:9px 18px`). `.btn.primary` = `background:var(--fg); color:var(--bg)`, `.btn.accent` = 청록, `.btn.ghost` = 테두리, `.btn.text` = 배경 없음. `.panel` 반경 `var(--r)`, `.chip` 시안 값. 폼은 시안 `common.css` 224–234 · 296–302(입력칸 · 선택 상자). 200줄 넘으면 폼 부분을 `forms.css`로 나눈다.

- [ ] **Step 6: layout.css** — 시안 `common.css`의 `.nav`~`.avatar`(22–45행 부근), `.head`~`.head-row`, `.subtabs`, 다크 블록의 `.theme-btn`. 헤더 배경은 `var(--nav-bg)`. 다크에서 `.btn.primary`, `.m.me` 글자색 `var(--bg)`.

- [ ] **Step 7: components.css** — 색 코드가 직접 적힌 곳이 있으면 토큰으로 바꾸고(`grep -n "#[0-9a-f]\{3,6\}" src/styles/*.css`로 tokens.css 말고는 0건이어야 함), 반경 8px → `10px`.

- [ ] **Step 8: 확인**
Run: `cd frontend && npm run build && npm run lint` → 둘 다 오류 0.
`grep -n "#[0-9a-fA-F]\{3,8\}" src/styles/*.css | grep -v tokens.css` → 출력 없음.
브라우저: 아무 화면에서 `document.documentElement.dataset.theme='dark'` → 배경 `rgb(17, 18, 20)`, 버튼 · 칩 글자가 읽힌다.

- [ ] **Step 9: Commit** — `git add frontend/index.html frontend/src/styles frontend/src/hooks/useTheme.ts frontend/src/components/layout/ThemeToggle.tsx frontend/src/main.tsx` · `[new-screens] 디자인 토큰 · 다크모드 · 공통 클래스를 새 시안으로`

### Task 2: 로고 · 새 헤더

**Files:**
- Create: `src/components/layout/Logo.tsx`
- Modify: `src/components/layout/AppLayout.tsx`, `src/App.tsx`

**Interfaces:**
- Consumes: `<ThemeToggle />`, `session`(Task 3에서 `session.user()` 추가 — 이 작업에서는 아직 없으므로 이름 칸은 Task 3에서 붙인다)
- Produces: `AppLayout({ role: 'TEACHER' | 'STUDENT' })` — 역할별 메뉴와 오른쪽 링크를 안에서 고른다. `<Logo to={string} />`

- [ ] **Step 1: Logo** — 시안 헤더의 방패 SVG. 색은 `fill="var(--logo)"`, 흰 선은 `stroke="var(--surface)"`, 점은 `fill="var(--accent)"`. `<Link className="logo" to={to}>` + "ThinkGuard".
- [ ] **Step 2: AppLayout** — props를 `{ role }`로 바꾼다.
  - 교수자: 메뉴 `내 클래스(/teacher/classes)`, 오른쪽 `요금제(/teacher/plans)` · `마이페이지(/teacher/mypage)` · `로그아웃`(버튼: `logout()` 후 `/`로) · ThemeToggle.
  - 학생: 메뉴 `내 과제(/student/classes)` · `클래스 참여(/student/join)`, 오른쪽 `마이페이지(/student/mypage)` · `나가기`(같은 동작) · ThemeToggle.
  - 오른쪽 링크는 `NavLink className={({isActive}) => 'btn text' + (isActive ? ' on' : '')}`. 역할 글자(교수자 · 학생)는 없앤다.
  - `<main className="wrap">` 대신 `<Outlet />`만 두고, 각 화면이 `PageHead` 아래 `<main className="wrap page">`를 쓰게 한다(Task 4). 이 작업에서는 임시로 `<div className="wrap page"><Outlet/></div>`.
- [ ] **Step 3: App.tsx** — `TEACHER_NAV` · `STUDENT_NAV` 상수를 지우고 `<AppLayout role="TEACHER" />` / `role="STUDENT"`.
- [ ] **Step 4: 확인** — 빌드 · 린트. 브라우저 `/teacher/classes`(시드 교수자 로그인): 헤더에 "교수자" 글자 없음, 오른쪽 요금제 · 마이페이지 · 로그아웃 · 테마 버튼. 375px에서 가로 스크롤 없음(`document.documentElement.scrollWidth === innerWidth`).
- [ ] **Step 5: Commit** — `[new-screens] 방패 로고와 새 헤더(요금제 · 마이페이지 · 로그아웃 · 테마)`

### Task 3: 로그인 사용자 저장 · 헤더 이름

**Files:**
- Modify: `src/api/client.ts`, `src/api/auth.ts`, `src/components/layout/AppLayout.tsx`

**Interfaces:**
- Produces: `session.user(): { name: string; email: string } | null`, `session.save(token, role, user?)`, `session.clear()`가 사용자도 지움

- [ ] **Step 1: client.ts** — `USER_KEY = 'tg.user'`. `save(token, role, user?: {name: string; email: string})`가 있으면 JSON으로 저장. `user()`는 `JSON.parse`를 try로 감싸고 `name`·`email`이 문자열일 때만 돌려준다(`unknown`으로 받아 좁힘). `clear()`에 `removeItem(USER_KEY)`.
- [ ] **Step 2: auth.ts** — `keep`에서 `session.save(r.access_token, r.user.role, { name: r.user.name, email: r.user.email })`.
- [ ] **Step 3: AppLayout** — 교수자: `.who`에 `.avatar`(이름 첫 글자) + 이름. 없으면 "교수자". 학생: `listMyClasses`의 첫 `student_no`를 쓴다(`useQuery({queryKey:['my-classes'], queryFn: listMyClasses})`, 없으면 칸 숨김). 아바타는 학번 끝 두 자리.
- [ ] **Step 4: 확인** — 로그인 → 헤더 "김교수". 새로 고침 → 그대로. 로그아웃 → `/`, sessionStorage에 `tg.user` 없음.
- [ ] **Step 5: Commit** — `[new-screens] 로그인한 교수자 이름을 탭에 저장해 헤더에 표시`

### Task 4: 화면 머리(PageHead) · 수업 코드 복사

**Files:**
- Create: `src/components/PageHead.tsx`, `src/components/CopyCode.tsx`
- Modify: `src/components/layout/AppLayout.tsx`(임시 wrap 제거)

**Interfaces:**
- Produces:
```ts
type PageHeadProps = { eyebrow?: string; title: string; sub?: ReactNode; back?: { to: string; label: string }; actions?: ReactNode; children?: ReactNode /* 탭 등 머리 아래쪽 */ }
export default function PageHead(props: PageHeadProps): JSX.Element // <section className="head"><div className="wrap">…</div></section>
type CopyCodeProps = { code: string }
export default function CopyCode(props: CopyCodeProps): JSX.Element // <span className="code">{code}<button>복사 → 복사됨 ✓(1.5초)</button></span>
```
- [ ] **Step 1:** PageHead — `back`이 있으면 `← label` 링크, `.head-row` 안에 왼쪽(eyebrow · h1 · sub) / 오른쪽(actions), 그 아래 children.
- [ ] **Step 2:** CopyCode — `navigator.clipboard?.writeText(code)` 성공 시 1.5초 "복사됨 ✓". 클릭이 카드 링크로 번지지 않게 `e.preventDefault(); e.stopPropagation()`.
- [ ] **Step 3:** AppLayout은 `<Outlet />`만. 아직 PageHead를 쓰지 않는 화면이 여백 없이 붙지 않도록, 이후 작업 전까지 각 화면 최상위에 `className="wrap page"`가 없는 경우를 위해 layout.css에 `.page{padding-block:32px 80px}`를 두고, 모든 기존 화면 최상위 요소를 `<main className="wrap page">`로 감싼다(이 작업에서 일괄: teacher · student 페이지 파일의 최상위 JSX만).
- [ ] **Step 4: 확인** — 빌드 · 린트, 교수자 · 학생 모든 경로가 여백 있게 보임.
- [ ] **Step 5: Commit** — `[new-screens] 화면 머리와 수업 코드 복사 조각`

### Task 5: 메인 스크롤 화면

**Files:**
- Modify: `src/pages/HomePage.tsx`
- Create: `src/pages/home/HomeNav.tsx`, `HomeHero.tsx`, `FeatureCards.tsx`, `TeacherBand.tsx`, `StudentSteps.tsx`, `Principles.tsx`, `PricingCards.tsx`, `HomeFooter.tsx`, `useReveal.ts`, `src/styles/home.css`, `src/styles/home-demo.css`

**Interfaces:**
- Consumes: `<Logo>`, `<ThemeToggle>`, `listPlans`(요금제 카드 금액)
- Produces: `useReveal(): void` — `.reveal` 요소에 IntersectionObserver로 `.in`을 붙인다.

- [ ] **Step 1:** 시안 `main_page_design.html`의 `<style>`을 `home.css`(헤더 · 히어로 · 섹션 · 요금제 · 푸터)와 `home-demo.css`(채팅 · 터미널 · 이해 확인 · 리포트 미니 화면, 교수자 띠)로 나눠 옮긴다. 색 코드는 토큰으로(`#7fd6c8` 같은 문법 강조색은 tokens.css에 `--syn-k` `--syn-s` `--syn-g`로 추가). 다크 규칙(`.dark-band` 배경 `var(--surface)` + 테두리)도 옮긴다.
- [ ] **Step 2:** 섹션마다 컴포넌트 하나. 문구는 시안 그대로("AI와 함께 스스로 생각하는 과제" 유지). 링크: 로그인 `/login`, 수업 코드로 입장 `/student/join`, 교수자로 시작하기 `/signup`, 요금제 카드 버튼 `/login?plan=SMALL|MEDIUM|LARGE`, 기능 카드는 링크 없이 `div`.
- [ ] **Step 3:** 채팅 예시 돌리기 · 교수자 패널 탭은 `useState` + `useEffect`(`setInterval` 4.2초, 정리 함수에서 `clearInterval`). `prefers-reduced-motion`이면 돌리지 않는다.
- [ ] **Step 4:** PricingCards는 `listPlans()` 결과로 그린다(로딩 중엔 시안 금액 대신 빈 카드 3개 높이 유지). 백엔드 연결 칩은 뺀다.
- [ ] **Step 5: 확인** — 빌드 · 린트. `/`를 1280 · 375에서 스크롤: 섹션이 나타나고 가로 스크롤 없음, 다크에서 교수자 띠가 배경과 구분.
- [ ] **Step 6: Commit** — `[new-screens] 메인을 스크롤 화면으로`

### Task 6: 로그인 / 계정 만들기 탭

**Files:**
- Create: `src/pages/auth/AuthPage.tsx`, `src/pages/auth/LoginForm.tsx`, `src/pages/auth/SignupForm.tsx`
- Delete: `src/pages/auth/LoginPage.tsx`, `src/pages/auth/SignupPage.tsx`(폼으로 옮긴 뒤)
- Modify: `src/App.tsx`

**Interfaces:**
- Produces: `AuthPage({ tab: 'login' | 'signup' })`, `LoginForm({ onDone: () => void })`, `SignupForm({ onDone: () => void })`

- [ ] **Step 1:** 지금 LoginPage · SignupPage의 폼 · mutation을 각각 LoginForm · SignupForm으로 옮긴다(signup 호출 그대로). LoginPage의 기본값 `teacher@school.ac.kr` / `password`는 빈 값으로(시드 계정과 달라 헷갈림).
- [ ] **Step 2:** AuthPage — 시안 `login.html` 구조: 가운데 카드, 위에 `.seg` 탭(로그인 · 계정 만들기), 아래 "학생은 수업 코드로 입장" 링크. 탭 전환은 `navigate('/login' | '/signup' + location.search, { replace: true })`. `onDone`: `?plan=`이 있으면 `/teacher/classes/new?plan=…`, 없으면 `/teacher/classes`.
- [ ] **Step 3:** App.tsx — `/login` → `<AuthPage tab="login" />`, `/signup` → `<AuthPage tab="signup" />`. 이 화면 헤더는 메인과 같은 `HomeNav`를 쓴다.
- [ ] **Step 4: 확인** — 시드 계정 로그인 → 내 클래스. `/login?plan=MEDIUM` 로그인 → 클래스 개설에 Medium 선택됨. 잘못된 비밀번호 → 오류 문구.
- [ ] **Step 5: Commit** — `[new-screens] 로그인과 계정 만들기를 한 화면의 탭으로`

### Task 7: 교수자 내 클래스(대시보드)

**Files:**
- Create: `src/hooks/useTeacherOverview.ts`, `src/pages/teacher/overview/StatTiles.tsx`, `TodoList.tsx`, `ClassCard.tsx`, `src/styles/pages.css`
- Modify: `src/pages/teacher/ClassListPage.tsx`, `src/main.tsx`(pages.css import)

**Interfaces:**
- Consumes: `listClasses`, `listAssignments(classId)`, `listJoinRequests(classId)`, `PageHead`, `CopyCode`
- Produces:
```ts
export type TodoItem = { kind: 'GRADING' | 'JOIN' | 'DUE'; title: string; meta: string; to: string }
export type ClassOverview = { info: ClassInfo; assignments: AssignmentSummary[]; requests: JoinRequest[] }
export function useTeacherOverview(): {
  isPending: boolean; error: Error | null
  classes: ClassOverview[]
  stats: { classes: number; students: number; openAssignments: number; grading: number }
  todos: TodoItem[]
}
```
- [ ] **Step 1:** 훅 — `useQuery(listClasses)` 후 `useQueries`로 클래스마다 `['assignments', id]` · `['join-requests', id]`, 그리고 `status !== 'DRAFT'`인 과제마다 `['grading', assignmentId]`(`getGradingList`). 채점 대기 = `GradingItem.score === null`인 수(`AssignmentSummary.todo`는 백엔드가 아직 늘 `null`이라 쓰지 않는다). 할 일: 채점 대기 > 0인 과제마다 GRADING(`…/assignments/:id/grading`, meta "클래스 · 과제 · 문항 n"), 참여 요청 있는 클래스마다 JOIN(`…/students`, meta 학번들 · 다시 입장 여부), 마감 7일 이내 OPEN 과제마다 DUE(`…/dashboard?assignment=:id`, title `마감 n일 전 · 제출 a / b명`). `stats.openAssignments` = `status === 'OPEN'` 수, `stats.students` = `student_count` 합.
- [ ] **Step 2:** 화면 — PageHead(eyebrow "Dashboard", title `${name}님, 안녕하세요`, sub `지금 확인할 일이 n건 있어요` 또는 `확인할 일이 없어요`, actions `+ 클래스 개설`). StatTiles 4칸(채점 대기 > 0이면 `.alert`). TodoList(없으면 "지금 할 일이 없어요"). ClassCard 격자 + 점선 "새 클래스 개설" 카드. 상태 칩: 시작 전(`now < starts_at`) · 진행 중 · 만료(`now >= expires_at`).
- [ ] **Step 3: 확인** — 시드: 클래스 2 · 학생 5 · 진행 중 과제 1 · 채점 대기 수가 채점 화면 수와 같음. 클래스 없는 새 교수자(계정 만들기로 확인): 빈 문구, 오류 없음.
- [ ] **Step 4: Commit** — `[new-screens] 교수자 내 클래스를 대시보드로(숫자 · 지금 할 일 · 클래스 카드)`

### Task 8: 요금제 화면(카드만)

**Files:**
- Modify: `src/pages/teacher/PlansPage.tsx`, `src/pages/teacher/plans/PlanCard.tsx`
- Delete: `src/pages/teacher/plans/ExtendList.tsx`(마이페이지에서 화면만 다시 만든다, Task 12)

- [ ] **Step 1:** 시안 `pricing.html`: PageHead(eyebrow "Pricing", "요금제", sub "클래스 하나 · 1년 · 기능은 모두 같아요", actions "클래스 만들러 가기 →" `/teacher/classes/new`). `listPlans()` 카드 3개, 버튼 "이 요금제로 만들기" → `/teacher/classes/new?plan=CODE`. 아래 note "결제는 클래스를 만들 때 해요 · 기간이 끝나면 마이페이지에서 연장". `payMock` · 결제 버튼 없음.
- [ ] **Step 2: 확인** — 빌드 · 린트, 버튼이 개설 화면에 그 요금제를 넘김.
- [ ] **Step 3: Commit** — `[new-screens] 요금제 화면은 카드만 두고 결제는 개설 때로`

### Task 9: 클래스 개설(결제하고 개설)

**Files:**
- Modify: `src/pages/teacher/ClassCreatePage.tsx`
- Create: `src/pages/teacher/PlanPicker.tsx`

**Interfaces:**
- Produces: `PlanPicker({ plans: Plan[]; value: PlanCode; onChange: (p: PlanCode) => void })` — 시안 `.opt` 카드 3개(라디오 역할, `role="radiogroup"`)

- [ ] **Step 1:** 시안 `teacher-class-new.html`: PageHead(back 내 클래스, eyebrow "New class", "클래스 개설"). 클래스 이름 · 시작 날짜 · PlanPicker · 요약 줄(`YYYY.MM.DD – +1년 · 학생 n명 · 금액`) · 버튼 "결제하고 개설".
- [ ] **Step 2:** mutation은 지금처럼 `payMock NEW → createClass`(`?payment=` 경로는 요금제 화면 결제가 없어졌으므로 지운다). `onSuccess`: `invalidateQueries(['classes'])` 후 `navigate('/teacher/classes/' + c.seq)`. 진행 중이면 버튼 비활성 + "개설 중…". 실패하면 `error-text` 표시하고 머문다. 이름이 비면 비활성.
- [ ] **Step 3: 확인** — 개설 → 클래스 상세로 이동, 수업 코드 보임. 버튼 연타해도 클래스 하나만 생김(`/classes` 개수 확인).
- [ ] **Step 4: Commit** — `[new-screens] 클래스 개설을 결제하고 개설 한 번으로`

### Task 10: 클래스 머리 · 탭(상세 · 학생 관리 · AI 기본값)

**Files:**
- Create: `src/pages/teacher/ClassHeader.tsx`
- Modify: `src/pages/teacher/ClassDetailPage.tsx`, `src/pages/teacher/AiSettingsPage.tsx`, `src/pages/teacher/students/ClassStudentsPage.tsx`(맨 바깥에 ClassHeader만 더함), `src/pages/teacher/AssignmentCard.tsx`

**Interfaces:**
- Consumes: `getClass`, `listJoinRequests`, `PageHead`, `CopyCode`
- Produces: `ClassHeader({ classId: number; tab: 'assignments' | 'students' | 'ai' })`

- [ ] **Step 1:** ClassHeader — 시안 `teacher-class.html` 머리: back 내 클래스, 상태 · 요금제 칩, 이름, `기간 · 남은 기간 n일`, actions(CopyCode + "+ 새 과제 만들기"), children `.subtabs`(과제 `/teacher/classes/:id` · 학생 `…/students` + 요청 수 칩 · AI 기본값 `…/ai-settings`).
- [ ] **Step 2:** ClassDetailPage — ClassHeader + 숫자 4칸(학생 n/상한 · 과제 수 · 최종 제출 합 · 채점 대기) + 과제 카드 목록 + 학생 칩. 학생 칩 링크의 `?assignment=a1`을 **배포된 첫 과제 번호**로(없으면 링크 대신 글자만). AssignmentCard는 시안 `.acard`(제목 · 칩 · meta · 제출 진행 막대 · 리포트/채점(대기 수)/설정/결과 공개).
- [ ] **Step 3:** AiSettingsPage · ClassStudentsPage — 최상위에 `<ClassHeader tab=…/>`를 두고 기존 내용은 `<main className="wrap page">` 안에 그대로. ClassStudentsPage · StudentList의 표 구조는 바꾸지 않는다(S6 칸 없음).
- [ ] **Step 4: 확인** — 세 탭 이동, 요청 수 칩, 학생 칩 → 학생 기록이 열림(오류 없음).
- [ ] **Step 5: Commit** — `[new-screens] 클래스 머리와 과제 · 학생 · AI 기본값 탭`

### Task 11: 과제 만들기 · 채점 · 리포트 · 학생 기록 모양

**Files:**
- Modify: `src/pages/teacher/editor/AssignmentEditorPage.tsx`, `Stepper.tsx`, `StepLoad.tsx`, `policy/PolicyOptions.tsx`, `questions/QuestionEditor.tsx`, `src/pages/teacher/grading/GradingPage.tsx`, `src/pages/teacher/report/DashboardPage.tsx`, `src/pages/teacher/StudentRecordPage.tsx`, `src/styles/screens.css`

- [ ] **Step 1:** 네 화면 모두 PageHead(back = 클래스, eyebrow 시안 값: "New assignment" · "Grading" · "Report" · "Record"). 리포트 · 기록 · 채점의 표 · 막대는 시안 `common.css` 258–295 규칙으로 screens.css를 맞춘다.
- [ ] **Step 2:** StepLoad에 **마감**(`<input type="datetime-local">`, `due_at`) 입력을 추가. `components/format.ts`에 두 함수를 더한다:
```ts
/** ISO(어느 시간대든) → datetime-local 값 "YYYY-MM-DDTHH:mm" (한국 시간) */
export const toKstLocalInput = (iso: string | null): string =>
  iso ? new Date(new Date(iso).getTime() + 9 * 3600_000).toISOString().slice(0, 16) : ''
/** datetime-local 값(한국 시간으로 본다) → "YYYY-MM-DDTHH:mm:00+09:00". 빈 값이면 null */
export const fromKstLocalInput = (v: string): string | null => (v ? `${v}:00+09:00` : null)
```
  저장 뒤 다시 열었을 때 같은 시각이 보이면 된다(시드 과제 마감 `2026-12-05T23:59` 확인).
- [ ] **Step 3:** PolicyOptions에 **AI 메시지 · 학생당**(`policy.usage_limit`, `type="number" min=1 max=200`) 입력을 추가. 저장 값은 정수.
- [ ] **Step 4:** QuestionEditor를 접었다 펴는 목록으로: 머리줄(번호 · 제목 첫 줄 · 유형 칩 · 채점 방식 · AI 켬/끔 · 배점)을 누르면 펼침. 기본은 첫 문항만 펼침. 편집 동작은 그대로.
- [ ] **Step 5: 확인** — 시드 과제 편집 4단계 이동 · 저장 후 다시 열면 마감 · AI 메시지 수 유지. 채점 · 리포트 · 기록 화면 오류 없음.
- [ ] **Step 6: Commit** — `[new-screens] 과제 만들기 · 채점 · 리포트 · 학생 기록을 새 모양으로(마감 · AI 메시지 수 입력)`

### Task 12: 교수자 마이페이지

**Files:**
- Create: `src/api/payments.ts`, `src/pages/teacher/mypage/TeacherMyPage.tsx`, `AccountSection.tsx`, `PasswordSection.tsx`, `UsageSection.tsx`, `PaymentHistory.tsx`, `src/components/SideNav.tsx`
- Modify: `src/App.tsx`

**Interfaces:**
- Produces:
```ts
// api/payments.ts — 결제 내역은 예시 데이터(결정 11/27, API 없음)
export type PaymentHistoryRow = { date: string; title: string; plan: PlanCode; student_limit: number; amount: number }
export const listPaymentHistory = (): Promise<PaymentHistoryRow[]> => Promise.resolve(EXAMPLE_ROWS)
// SideNav: 섹션 앵커 목록 + 스크롤 위치 표시
type SideNavProps = { items: { id: string; label: string }[]; logoutLabel: string; onLogout: () => void }
```
- [ ] **Step 1:** payments.ts — 예시 2줄(시안 값). 화면은 `useQuery({queryKey:['payment-history'], queryFn: listPaymentHistory})`.
- [ ] **Step 2:** SideNav — 시안 `teacher-mypage.html`의 스크롤 따라 강조(스크립트를 `useEffect` + scroll 리스너로, 정리 함수에서 제거).
- [ ] **Step 3:** 섹션 — 계정 정보(`session.user()` 이름 · 이메일 읽기 전용 칸, "저장" 버튼은 누르면 `저장은 아직 지원하지 않아요` 안내 문구), 비밀번호 변경(입력 3칸 + 버튼, 같은 안내), 이용 중인 클래스(`listClasses` 표 + "1년 연장" 버튼 — 같은 안내), 결제 내역(표 + 칩 "예시 데이터 · 실제 결제 없음"), 로그아웃.
- [ ] **Step 4:** App.tsx — `/teacher/mypage` 경로.
- [ ] **Step 5: 확인** — 헤더 마이페이지 → 이름 · 이메일 · 클래스 2개 · 예시 결제 2줄. 저장 · 연장 버튼이 아무 요청도 보내지 않음(네트워크 탭 확인).
- [ ] **Step 6: Commit** — `[new-screens] 교수자 마이페이지(계정 · 비밀번호 · 이용 중인 클래스 · 결제 내역 예시)`

### Task 13: 학생 입장 · 내 과제

**Files:**
- Modify: `src/pages/student/JoinClassPage.tsx`, `src/pages/student/StudentClassPage.tsx`
- Create: `src/pages/student/ConsentCard.tsx`, `src/pages/student/TaskCard.tsx`

**Interfaces:**
- Consumes: `joinClass`, `getMyEnrollment`, `acceptConsent`, `listMyClasses`, `session.token()`
- Produces: `ConsentCard({ classId: number; className: string; onDone: () => void })`(ConsentPage도 이것을 쓴다), `TaskCard({ classId, assignment })`

- [ ] **Step 1:** JoinClassPage — 단계 `'form' | 'consent' | 'pending'`. 입장 APPROVED → consent 단계(ConsentCard, 동의 → `/student/classes`, 동의 안 함 → "입장하지 않았어요" + 다시 보기). PENDING → 대기(지금 문구 · "수락됐는지 확인"; APPROVED가 되면 consent 단계). 학생 토큰이 이미 있으면(`session.role()==='STUDENT'`) 학번 칸 대신 `listMyClasses` 첫 학번을 쓰고 "학번 n로 들어가요" 표시.
- [ ] **Step 2:** ConsentPage — ConsentCard 재사용(문구 시안 `student-join.html` 동의 카드).
- [ ] **Step 3:** StudentClassPage — PageHead(eyebrow "My assignments", "내 과제", sub "진행 중인 과제 n개 · 가장 가까운 마감 M월 D일(요일)", actions "+ 다른 클래스 참여"). 클래스별 묶음 + TaskCard(상태 칩 · meta · 문항 제출 진행 막대 · D-day · 단계 버튼 · 흐름 막대). 흐름 단계는 `listMyClasses` 과제의 `status`로만 정한다: `IN_PROGRESS` = 01 문항 풀기(버튼 "이어서 풀기" → 풀이), `FINALIZED` = 03 이해 확인(버튼 "이해 확인" → `…/check`; 이미 냈으면 그 화면이 "제출했어요"를 보여 준다), `RELEASED` = 04 내 리포트(버튼 "내 리포트", "끝난 과제" 칸). 진행 막대는 `submitted / total`, 점수는 `score_text`가 있을 때만. 결과 공개된 과제는 "끝난 과제" 칸으로. 참여 대기 중인 클래스는 안내 문구.
- [ ] **Step 4: 확인** — 명단 학번 입장 → 동의 → 내 과제. 새 학번 → 대기 → (교수자 수락) → 동의. 참여 클래스 없음 → 빈 문구.
- [ ] **Step 5: Commit** — `[new-screens] 학생 입장 · 동의 · 대기를 한 화면으로, 내 과제 카드와 흐름 막대`

### Task 14: 과제 풀이 · 이해 확인 · 내 리포트 · 학생 마이페이지

**Files:**
- Modify: `src/pages/student/solve/SolvePage.tsx`, `QuestionNav.tsx`, `QuestionCard.tsx`, `ChatPanel.tsx`, `FinalizeBar.tsx`, `src/components/TestResults.tsx`, `src/pages/student/check/UnderstandingCheckPage.tsx`, `src/pages/student/MyReportPage.tsx`, `src/styles/screens.css`
- Create: `src/pages/student/StudentMyPage.tsx`
- Modify: `src/App.tsx`

- [ ] **Step 1:** SolvePage — PageHead(back 내 과제, 제목, sub 과목 · 언어 · 마감, actions 붙여넣기 안내 문구 · 판별 과정 체크박스), children = QuestionNav를 시안 `.qbar` 알약으로(낸 문항 ✓ · 유형 이름). 왼쪽 문항 카드 · 오른쪽 AI 패널(`position: sticky`), 아래 FinalizeBar 카드. **훅 호출 · 핸들러는 그대로**, JSX 감싸는 요소와 className만 바꾼다.
- [ ] **Step 2:** TestResults — 시안 표(✓/✗ · 입력 · 기대 출력 · 내 출력, 머리줄에 "a / b 통과" 칩).
- [ ] **Step 3:** 이해 확인 — PageHead(back 내 과제, eyebrow "Understanding check"), 위 숫자 3칸(도움 AI 없음 · 예상 시간 · 점수 자동 반영 안 됨), 제출 뒤 "이해 확인을 제출했어요" 상태 카드. 내 리포트 — PageHead + 시안 `student-report.html` 순서.
- [ ] **Step 4:** StudentMyPage — 시안 `student-mypage.html`: SideNav(내 정보 · 참여한 클래스 · 기록 안내 · 나가기), 내 정보(학번 · 탭 안내), 참여한 클래스 표(`listMyClasses`: 클래스 · 학번 · 상태 칩 · 과제 수), 기록 안내(ConsentCard 문구와 같은 항목, 읽기만). App.tsx에 `/student/mypage`.
- [ ] **Step 5: 확인** — 풀이: 문항 이동 · 공개 테스트 실행 · 제출 · 채팅 보내기 · 최종 제출이 전처럼 동작(네트워크 요청 모양 같음). 붙여넣기 → `/paste-events` 본문에 `length`만. 이해 확인 · 리포트 · 마이페이지 오류 없음.
- [ ] **Step 6: Commit** — `[new-screens] 과제 풀이 · 이해 확인 · 내 리포트를 새 모양으로, 학생 마이페이지`

### Task 15: 마무리 — 문서 상태 · 전체 확인

**Files:**
- Modify: `docs/planning/screens.md`(머리 상태 줄: v4 구현됨, 결정 S6 결과), `README.md`(화면 시안 링크를 `docs/planning/design/`로)

- [ ] **Step 1:** screens.md 상태 줄을 "v4 · 구현됨"으로, 화면 표의 파일 이름을 실제(AuthPage · TeacherMyPage · StudentMyPage …)로 고친다.
- [ ] **Step 2: 전체 확인**
Run: `cd frontend && npm run build && npm run lint` → 오류 0
Run: `cd backend && .venv/bin/pytest -q && .venv/bin/ruff check .` → 백엔드를 바꾸지 않았으므로 기존 그대로 통과
브라우저(시드 DB 사본으로): README 시연 순서 1–3을 라이트 · 다크, 1280 · 375px에서 한 번씩. 각 화면 `scrollWidth === innerWidth`.
- [ ] **Step 3: Commit** — `[new-screens] 화면 명세를 v4 구현 기준으로 고침`

---

## Self-Review 메모
- 스펙 대조: 공통(헤더 T2–3 · 다크 T1 · 메인 T5 · 로그인 탭 T6 · 화면 머리 T4), 교수자(대시보드 T7 · 요금제 T8 · 개설 T9 · 상세/탭 T10 · 만들기 마감·AI 메시지 T11 · 마이페이지 T12), 학생(입장 T13 · 내 과제 T13 · 풀이/확인/리포트 T14 · 마이페이지 T14). S6 칸은 넣지 않음(T10 Step 3).
- 시안의 예시 동작(sessionStorage 결과 공개, 토스트)은 옮기지 않는다 — 실제 API 동작을 쓴다.
