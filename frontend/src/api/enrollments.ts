import { mockEnrollments } from './mock/enrollmentStore'

/** 입장 방식. APPROVAL: 명단에 없는 학생은 참여 요청 → 교수자 수락 / OPEN: 코드만 있으면 바로 입장 */
export type JoinMode = 'APPROVAL' | 'OPEN'
export type EnrollmentStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'REMOVED'

export type JoinRequest = { invite_code: string; alias: string }
export type JoinResult = { class_id: string; class_name: string; status: 'APPROVED' | 'PENDING' }

/** 교수자가 보는 참여 요청 한 건 */
export type PendingRequest = { id: string; alias: string; requested_at: string }

/** 수업 전에 미리 넣어 두는 학생 명단(수업용 ID). 명단에 있으면 요청 없이 바로 입장 */
export type RosterSettings = { join_mode: JoinMode; roster: string[] }

/** 학생: 수업 코드로 참여. 오류: 없는 코드 · 정원 초과 · 만료 · 내보낸 학생 */
export const joinClass = (body: JoinRequest) => mockEnrollments.join(body)
/** 학생: 참여 요청이 수락됐는지 확인 */
export const getMyEnrollment = (classId: string) => mockEnrollments.mine(classId)
/** 첫 접속 기록 동의. 동의하지 않으면 AI 도움 과제를 이용할 수 없다 */
export const acceptConsent = (classId: string) => mockEnrollments.consent(classId)

/** 교수자: 참여 요청 목록 · 수락 · 거절 */
export const listJoinRequests = (classId: string) => mockEnrollments.requests(classId)
export const decideJoinRequest = (classId: string, requestId: string, approve: boolean) =>
  mockEnrollments.decide(classId, requestId, approve)
/** 교수자: 학생 내보내기. 제출 기록은 남고, 학생은 더 이상 과제·AI 도움에 들어올 수 없다 */
export const removeStudent = (classId: string, studentId: string) => mockEnrollments.remove(classId, studentId)
/** 교수자: 입장 방식과 미리 넣어 둔 명단 */
export const getRosterSettings = (classId: string) => mockEnrollments.roster(classId)
export const saveRosterSettings = (classId: string, body: RosterSettings) => mockEnrollments.saveRoster(classId, body)
