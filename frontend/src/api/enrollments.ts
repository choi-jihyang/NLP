import { api, del, get, post, put, REENTRY_TICKET_KEY, session } from './client'

/** 입장 방식. APPROVAL: 명단에 없는 학생은 참여 요청 → 교수자 수락 / OPEN: 코드만 있으면 바로 입장 */
export type JoinMode = 'APPROVAL' | 'OPEN'
export type EnrollmentStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'REMOVED'

export type JoinRequest = { invite_code: string; student_no: string }
export type JoinResult = {
  class_id: number
  class_name: string
  status: 'APPROVED' | 'PENDING'
  /** 다시 입장(같은 학번이 다른 탭 · 기기)이면 null이고 reentry_ticket이 온다 */
  access_token: string | null
  reentry_ticket: string | null
}

/** 교수자가 보는 참여 요청 한 건 */
export type PendingRequest = { seq: number; student_no: string; requested_at: string; is_reentry: boolean }

/** 수업 전에 미리 넣어 두는 학생 명단. 명단에서 빼면 지우지 않고 is_use = false */
export type RosterEntry = { student_no: string; is_use: boolean }
export type RosterSettings = { join_mode: JoinMode; roster: RosterEntry[] }

const TICKET_KEY = REENTRY_TICKET_KEY

/** 대기 중인 참여 요청 · 다시 입장 티켓 지우기(로그아웃 · 학번 다시 입력) */
export const clearReentryTicket = () => localStorage.removeItem(TICKET_KEY)

/**
 * 이 브라우저에서 입장했던 학번 기억(수업 코드 + 학번 → 그 계정 토큰).
 * 로그아웃은 화면에서 나가는 것일 뿐 수업에서 나가는 게 아니므로, 같은 브라우저에서 같은 코드 · 학번을 넣으면
 * 기억한 토큰으로 입장 요청을 보내 교수자 승인 없이 다시 들어간다(서버는 같은 계정의 재입장으로 처리).
 * 다른 브라우저 · 기기는 여전히 다시 입장 승인(schema D21).
 */
const REMEMBER_KEY = 'tg.remembered_students'
const LAST_JOIN_KEY = 'tg.last_join'
type Remembered = { code: string; student_no: string; token: string }

const norm = (b: JoinRequest): JoinRequest => ({ invite_code: b.invite_code.trim().toUpperCase(), student_no: b.student_no.trim() })

const readRemembered = (): Remembered[] => {
  try {
    const v: unknown = JSON.parse(localStorage.getItem(REMEMBER_KEY) ?? '[]')
    return Array.isArray(v) ? (v as Remembered[]) : []
  } catch {
    return []
  }
}

const remember = (b: JoinRequest, token: string) => {
  const { invite_code: code, student_no } = norm(b)
  const rest = readRemembered().filter((r) => !(r.code === code && r.student_no === student_no))
  localStorage.setItem(REMEMBER_KEY, JSON.stringify([...rest, { code, student_no, token }]))
}

const rememberedToken = (b: JoinRequest): string | undefined => {
  const { invite_code: code, student_no } = norm(b)
  return readRemembered().find((r) => r.code === code && r.student_no === student_no)?.token
}

/** 학생: 수업 코드로 참여. 오류: 없는 코드 · 정원 초과 · 만료 · 내보낸 학생 */
export const joinClass = async (body: JoinRequest): Promise<JoinResult> => {
  const kept = session.token() ? undefined : rememberedToken(body)
  const r = await api<JoinResult>('/enrollments', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: kept ? { Authorization: `Bearer ${kept}` } : undefined,
  })
  localStorage.setItem(LAST_JOIN_KEY, JSON.stringify(norm(body)))
  if (r.access_token) {
    session.save(r.access_token, 'STUDENT')
    remember(body, r.access_token)
  }
  if (r.reentry_ticket) localStorage.setItem(TICKET_KEY, r.reentry_ticket)
  return r
}

const lastJoin = (): JoinRequest | null => {
  try {
    const v: unknown = JSON.parse(localStorage.getItem(LAST_JOIN_KEY) ?? 'null')
    const b = v as Partial<JoinRequest> | null
    return b && typeof b.invite_code === 'string' && typeof b.student_no === 'string' ? (b as JoinRequest) : null
  } catch {
    return null
  }
}

/** 학생: 참여 요청이 수락됐는지 확인 (다시 입장 대기 중이면 티켓으로 토큰을 받는다) */
export const getMyEnrollment = async (classId: number): Promise<{ status: EnrollmentStatus }> => {
  const ticket = localStorage.getItem(TICKET_KEY)
  if (ticket && !session.token()) {
    const r = await post<{ status: EnrollmentStatus; access_token: string | null }>('/enrollments/reentry', { ticket })
    if (r.access_token) {
      session.save(r.access_token, 'STUDENT')
      localStorage.removeItem(TICKET_KEY)
      const last = lastJoin()
      if (last) remember(last, r.access_token)
    }
    return { status: r.status }
  }
  return get<{ status: EnrollmentStatus }>(`/enrollments/${classId}/me`)
}
/** 첫 접속 기록 동의. 동의하지 않으면 AI 도움 과제를 이용할 수 없다 */
export const acceptConsent = (classId: number) => post<{ ok: boolean }>(`/enrollments/${classId}/consent`)

/** 교수자: 참여 요청 목록 · 수락 · 거절 */
export const listJoinRequests = (classId: number) => get<PendingRequest[]>(`/classes/${classId}/join-requests`)
export const decideJoinRequest = (classId: number, enrollmentSeq: number, approve: boolean) =>
  post<unknown>(`/classes/${classId}/join-requests/${enrollmentSeq}`, { approve })
/** 교수자: 학생 내보내기. 제출 기록은 남고, 학생은 더 이상 과제·AI 도움에 들어올 수 없다 */
export const removeStudent = (classId: number, studentSeq: number) => del<unknown>(`/classes/${classId}/students/${studentSeq}`)
/** 교수자: 입장 방식과 미리 넣어 둔 명단 */
export const getRosterSettings = (classId: number) => get<RosterSettings>(`/classes/${classId}/roster`)
export const saveRosterSettings = (classId: number, body: RosterSettings) =>
  put<RosterSettings>(`/classes/${classId}/roster`, body)
