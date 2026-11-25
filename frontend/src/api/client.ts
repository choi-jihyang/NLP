/** 백엔드 호출 공통 함수. 개발 중에는 Vite 프록시가 /api → localhost:8000 으로 보낸다. */

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

/**
 * 로그인 · 입장 토큰. 탭마다 따로 둔다(sessionStorage) — 시연 때 교수자 탭과 학생 탭을 한 브라우저에서 같이 쓰기 위해.
 * 학생은 같은 탭을 닫았다 열면 다시 입장해야 한다(다시 입장은 대기 티켓, schema D21).
 */
const TOKEN_KEY = 'tg.access_token'
const ROLE_KEY = 'tg.role'

export type Role = 'TEACHER' | 'STUDENT'

export const session = {
  token: (): string | null => sessionStorage.getItem(TOKEN_KEY),
  role: (): Role | null => sessionStorage.getItem(ROLE_KEY) as Role | null,
  save(token: string, role: Role) {
    sessionStorage.setItem(TOKEN_KEY, token)
    sessionStorage.setItem(ROLE_KEY, role)
  },
  clear() {
    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(ROLE_KEY)
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
  if (!res.ok) throw await toError(res)
  return res.json() as Promise<T>
}

export const get = <T>(path: string) => api<T>(path)
export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
export const put = <T>(path: string, body: unknown) => api<T>(path, { method: 'PUT', body: JSON.stringify(body) })
export const del = <T>(path: string) => api<T>(path, { method: 'DELETE' })

/** 프론트 id(문자열) ↔ 백엔드 seq(숫자). 화면 코드는 문자열 id를 그대로 쓴다 */
export const sid = (seq: number | null | undefined): string => (seq == null ? 'new' : String(seq))
export const nid = (id: string): number => {
  const n = Number(id)
  if (!id || !Number.isInteger(n) || n <= 0) throw new ApiError(400, 'VALIDATION_FAILED', `잘못된 id: ${id}`)
  return n
}

/** 언어 표기: 백엔드 Enum(대문자) ↔ 화면 표기 */
const LANG_TO_UI = { C: 'C', PYTHON: 'Python', JAVA: 'Java', JAVASCRIPT: 'JavaScript' } as const
export type BackendLanguage = keyof typeof LANG_TO_UI
export type UiLanguage = (typeof LANG_TO_UI)[BackendLanguage]
export const langToUi = (l: BackendLanguage): UiLanguage => LANG_TO_UI[l]
export const langToApi = (l: UiLanguage): BackendLanguage =>
  (Object.keys(LANG_TO_UI) as BackendLanguage[]).find((k) => LANG_TO_UI[k] === l) ?? 'C'
