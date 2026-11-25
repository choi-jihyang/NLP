import { del, get, nid, post, put, session, sid } from './client'

/** 입장 방식. APPROVAL: 명단에 없는 학생은 참여 요청 → 교수자 수락 / OPEN: 코드만 있으면 바로 입장 */
export type JoinMode = 'APPROVAL' | 'OPEN'
export type EnrollmentStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'REMOVED'

export type JoinRequest = { invite_code: string; alias: string }
export type JoinResult = { class_id: string; class_name: string; status: 'APPROVED' | 'PENDING' }

/** 교수자가 보는 참여 요청 한 건 */
export type PendingRequest = { id: string; alias: string; requested_at: string }

/** 수업 전에 미리 넣어 두는 학생 명단(수업용 ID). 명단에 있으면 요청 없이 바로 입장 */
export type RosterSettings = { join_mode: JoinMode; roster: string[] }

type JoinOut = {
  class_id: number
  class_name: string
  status: 'APPROVED' | 'PENDING'
  access_token: string | null
  reentry_ticket: string | null
}
type RosterOut = { join_mode: JoinMode; roster: { student_no: string; is_use: boolean }[] }

/** 다시 입장(대기 티켓) — 같은 학번이 다른 탭 · 기기에서 들어오면 교수자 수락 뒤 토큰을 받는다(schema D21) */
const TICKET_KEY = 'tg.reentry_ticket'

/** 학생: 수업 코드로 참여. 오류: 없는 코드 · 정원 초과 · 만료 · 내보낸 학생 */
export const joinClass = async (body: JoinRequest): Promise<JoinResult> => {
  const r = await post<JoinOut>('/enrollments', { invite_code: body.invite_code, student_no: body.alias })
  if (r.access_token) session.save(r.access_token, 'STUDENT')
  if (r.reentry_ticket) sessionStorage.setItem(TICKET_KEY, r.reentry_ticket)
  return { class_id: sid(r.class_id), class_name: r.class_name, status: r.status }
}

/** 학생: 참여 요청이 수락됐는지 확인 (다시 입장 대기 중이면 티켓으로 토큰을 받는다) */
export const getMyEnrollment = async (classId: string): Promise<{ status: EnrollmentStatus }> => {
  const ticket = sessionStorage.getItem(TICKET_KEY)
  if (ticket && !session.token()) {
    const r = await post<{ status: EnrollmentStatus; access_token: string | null }>('/enrollments/reentry', { ticket })
    if (r.access_token) {
      session.save(r.access_token, 'STUDENT')
      sessionStorage.removeItem(TICKET_KEY)
    }
    return { status: r.status }
  }
  return get<{ status: EnrollmentStatus }>(`/enrollments/${nid(classId)}/me`)
}
/** 첫 접속 기록 동의. 동의하지 않으면 AI 도움 과제를 이용할 수 없다 */
export const acceptConsent = (classId: string) => post<{ ok: boolean }>(`/enrollments/${nid(classId)}/consent`)

/** 교수자: 참여 요청 목록 · 수락 · 거절 */
export const listJoinRequests = async (classId: string): Promise<PendingRequest[]> =>
  (await get<{ seq: number; student_no: string; requested_at: string }[]>(`/classes/${nid(classId)}/join-requests`)).map(
    (r) => ({ id: sid(r.seq), alias: r.student_no, requested_at: r.requested_at }),
  )
export const decideJoinRequest = (classId: string, requestId: string, approve: boolean) =>
  post<unknown>(`/classes/${nid(classId)}/join-requests/${nid(requestId)}`, { approve })
/** 교수자: 학생 내보내기. 제출 기록은 남고, 학생은 더 이상 과제·AI 도움에 들어올 수 없다 */
export const removeStudent = (classId: string, studentId: string) =>
  del<unknown>(`/classes/${nid(classId)}/students/${nid(studentId)}`)
/** 교수자: 입장 방식과 미리 넣어 둔 명단 (화면은 사용 중인 학번만 다룬다) */
export const getRosterSettings = async (classId: string): Promise<RosterSettings> => {
  const r = await get<RosterOut>(`/classes/${nid(classId)}/roster`)
  return { join_mode: r.join_mode, roster: r.roster.filter((m) => m.is_use).map((m) => m.student_no) }
}
export const saveRosterSettings = async (classId: string, body: RosterSettings): Promise<RosterSettings> => {
  const r = await put<RosterOut>(`/classes/${nid(classId)}/roster`, {
    join_mode: body.join_mode,
    roster: body.roster.map((student_no) => ({ student_no, is_use: true })),
  })
  return { join_mode: r.join_mode, roster: r.roster.filter((m) => m.is_use).map((m) => m.student_no) }
}
