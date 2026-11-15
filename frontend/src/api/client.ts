/** 백엔드 호출 공통 함수. 개발 중에는 Vite 프록시가 /api → localhost:8000 으로 보낸다. */

export class ApiError extends Error {
  readonly status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  // TODO: 로그인 구현 시 JWT를 Authorization 헤더에 추가

  const res = await fetch(`/api${path}`, { ...init, headers })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json() as Promise<T>
}
