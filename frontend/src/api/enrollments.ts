import { del, get, post, put, REENTRY_TICKET_KEY, session } from './client'

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
export const clearReentryTicket = () => sessionStorage.removeItem(TICKET_KEY)

/** 학생: 수업 코드로 참여. 오류: 없는 코드 · 정원 초과 · 만료 · 내보낸 학생 */
export const joinClass = async (body: JoinRequest): Promise<JoinResult> => {
  const r = await post<JoinResult>('/enrollments', body)
  if (r.access_token) session.save(r.access_token, 'STUDENT')
  if (r.reentry_ticket) sessionStorage.setItem(TICKET_KEY, r.reentry_ticket)
  return r
}

/** 학생: 참여 요청이 수락됐는지 확인 (다시 입장 대기 중이면 티켓으로 토큰을 받는다) */
export const getMyEnrollment = async (classId: number): Promise<{ status: EnrollmentStatus }> => {
  const ticket = sessionStorage.getItem(TICKET_KEY)
  if (ticket && !session.token()) {
    const r = await post<{ status: EnrollmentStatus; access_token: string | null }>('/enrollments/reentry', { ticket })
    if (r.access_token) {
      session.save(r.access_token, 'STUDENT')
      sessionStorage.removeItem(TICKET_KEY)
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
