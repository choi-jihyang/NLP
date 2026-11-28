/** 백엔드 호출 공통 함수. 개발 중에는 Vite 프록시가 /api → localhost:8000 으로 보낸다.
 * 타입은 백엔드 응답 모양 그대로(docs/spec/api-contract.md): id는 seq(숫자), Enum은 대문자.
 */

export class ApiError extends Error {
  readonly status: number
  /** 백엔드 에러 코드 (docs/spec/error-handling.md). 예: CLASS_FULL, ALREADY_SUBMITTED */
  readonly code: string
  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

export type Role = 'TEACHER' | 'STUDENT'

/**
 * 로그인 · 입장 토큰.
 * - 교수자: 탭마다 따로 둔다(sessionStorage) — 시연 때 교수자 탭과 학생 탭을 한 브라우저에서 같이 쓰기 위해.
 * - 학생: 브라우저에 남긴다(localStorage) — 탭이나 브라우저를 닫았다 열어도 로그아웃하기 전까지 입장 상태가 유지된다.
 *   토큰은 클래스 이용 기간까지 유효하다. 다른 브라우저 · 기기에서는 여전히 다시 입장(대기 티켓, schema D21).
 * 이 탭에 교수자 로그인이 있으면 그것을 먼저 쓴다.
 */
const TOKEN_KEY = 'tg.access_token'
const ROLE_KEY = 'tg.role'
const USER_KEY = 'tg.user'
/** 학생 참여 요청 대기 · 다시 입장 티켓 (api/enrollments.ts가 쓴다). 학생 토큰처럼 localStorage */
export const REENTRY_TICKET_KEY = 'tg.reentry_ticket'

/** 로그인한 교수자 이름 · 이메일. 헤더 · 마이페이지에 쓴다(새 API 없이 로그인 응답을 저장) */
export type SessionUser = { name: string; email: string }

/** 이 탭에서 쓰는 저장소: 교수자 로그인이 있으면 sessionStorage, 없으면 학생용 localStorage */
const store = (): Storage => (sessionStorage.getItem(TOKEN_KEY) ? sessionStorage : localStorage)

const readUser = (): SessionUser | null => {
  try {
    const v: unknown = JSON.parse(store().getItem(USER_KEY) ?? 'null')
    if (typeof v !== 'object' || v === null) return null
    const { name, email } = v as Record<string, unknown>
    return typeof name === 'string' && typeof email === 'string' ? { name, email } : null
  } catch {
    return null
  }
}

export const session = {
  token: (): string | null => store().getItem(TOKEN_KEY),
  role: (): Role | null => store().getItem(ROLE_KEY) as Role | null,
  user: readUser,
  save(token: string, role: Role, user?: SessionUser) {
    const s = role === 'STUDENT' ? localStorage : sessionStorage
    s.setItem(TOKEN_KEY, token)
    s.setItem(ROLE_KEY, role)
    if (user) s.setItem(USER_KEY, JSON.stringify(user))
  },
  /** 이 탭에서 쓰던 로그인만 지운다(교수자 탭에서 로그아웃해도 학생 입장은 남는다) */
  clear() {
    const s = store()
    s.removeItem(TOKEN_KEY)
    s.removeItem(ROLE_KEY)
    s.removeItem(USER_KEY)
  },
}

async function toError(res: Response): Promise<ApiError> {
  const text = await res.text()
  try {
    const body = JSON.parse(text) as { code?: string; message?: string }
    return new ApiError(res.status, body.code ?? 'ERROR', body.message ?? text)
  } catch {
    return new ApiError(res.status, 'ERROR', text || res.statusText)
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const isForm = init.body instanceof FormData
  if (init.body && !isForm && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const token = session.token()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(`/api${path}`, { ...init, headers })
  if (res.status === 401 && token) expire()
  if (!res.ok) throw await toError(res)
  return res.json() as Promise<T>
}

/**
 * 로그인했는데 서버가 401(토큰 만료 · 서버 DB가 바뀜 등)을 주면: 이 탭의 로그인 정보를 지우고 로그인 화면으로.
 * 페이지를 새로 열어서 화면이 기억한 데이터도 함께 지운다.
 */
function expire() {
  const role = session.role()
  session.clear()
  if (role === 'STUDENT') localStorage.removeItem(REENTRY_TICKET_KEY)
  window.location.assign(role === 'STUDENT' ? '/student/join?expired=1' : '/login?expired=1')
}

export const get = <T>(path: string) => api<T>(path)
export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
export const put = <T>(path: string, body: unknown) => api<T>(path, { method: 'PUT', body: JSON.stringify(body) })
export const del = <T>(path: string) => api<T>(path, { method: 'DELETE' })

/** URL 경로 파라미터(문자열) → seq. 숫자가 아니면 요청하지 않고 오류 */
export const toSeq = (value: string | undefined | null): number => {
  const n = Number(value)
  if (!value || !Number.isInteger(n) || n <= 0) throw new ApiError(400, 'VALIDATION_FAILED', `잘못된 번호: ${value}`)
  return n
}

/** 과제 언어(백엔드 Enum)와 화면 표기 */
export type Language = 'C' | 'PYTHON' | 'JAVA' | 'JAVASCRIPT'
export const LANGUAGE_LABEL: Record<Language, string> = { C: 'C', PYTHON: 'Python', JAVA: 'Java', JAVASCRIPT: 'JavaScript' }
