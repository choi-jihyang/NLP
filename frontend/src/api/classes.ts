import type { AiPolicy, HintMode } from './assignments'
import { get, langToUi, nid, post, put, sid, type BackendLanguage } from './client'
import { buyNewPass, type PlanCode } from './plans'

export type ClassInfo = {
  id: string
  name: string
  invite_code: string
  student_count: number
  student_limit: number
  plan: PlanCode
  expires_at: string
}

export type ClassStudent = { id: string; alias: string }

/** 학생 "내 과제" 화면의 한 줄 */
export type MyAssignment = {
  id: string
  title: string
  language: string
  /** 푸는 중 → 최종 제출(결과 공개 전) → 결과 공개 */
  status: 'IN_PROGRESS' | 'FINALIZED' | 'RELEASED'
  due_at: string | null
  hint_mode: HintMode
  hint_mode_label: string
  submitted: number
  total: number
  /** 결과가 공개된 뒤에만 채워진다 */
  score_text: string | null
}

export type MyClass = {
  class_id: string
  class_name: string
  alias: string
  /** 참여 요청이 아직 수락되지 않았으면 PENDING (과제는 비어 있다) */
  enrollment_status: 'APPROVED' | 'PENDING'
  assignments: MyAssignment[]
}

/** 학생 수 상한은 요금제가 정한다 */
export type ClassCreate = { name: string; plan: PlanCode }

type ClassOut = Omit<ClassInfo, 'id'> & { seq: number; starts_at: string }
type MyAssignmentOut = Omit<MyAssignment, 'id' | 'language'> & { seq: number; language: BackendLanguage }
type MyClassOut = {
  class_id: number
  class_name: string
  student_no: string
  enrollment_status: 'APPROVED' | 'PENDING'
  assignments: MyAssignmentOut[]
}

const toClass = ({ seq, ...c }: ClassOut): ClassInfo => ({ ...c, id: sid(seq) })

/** 오늘 날짜(한국 시간) YYYY-MM-DD */
const todayKst = () => new Date(Date.now() + 9 * 3600_000).toISOString().slice(0, 10)

export const listClasses = async () => (await get<ClassOut[]>('/classes')).map(toClass)
/** 클래스 개설. 결제 목업(NEW) 이용권을 먼저 만들고, 오늘부터 시작하는 클래스로 연다. 수업 코드가 새로 발급된다 */
export const createClass = async (body: ClassCreate) => {
  const payment_seq = await buyNewPass(body.plan)
  return toClass(await post<ClassOut>('/classes', { name: body.name, starts_on: todayKst(), payment_seq }))
}
/** 이 클래스에서 새로 만드는 과제에 미리 채울 AI 도움 정책 */
export const getAiDefaults = (classId: string) => get<AiPolicy>(`/classes/${nid(classId)}/ai-defaults`)
export const saveAiDefaults = (classId: string, policy: AiPolicy) =>
  put<AiPolicy>(`/classes/${nid(classId)}/ai-defaults`, policy)
export const getClass = async (classId: string) => toClass(await get<ClassOut>(`/classes/${nid(classId)}`))
export const listStudents = async (classId: string): Promise<ClassStudent[]> =>
  (await get<{ seq: number; student_no: string }[]>(`/classes/${nid(classId)}/students`)).map((s) => ({
    id: sid(s.seq),
    alias: s.student_no,
  }))
/** 학생: 참여한 클래스와 과제 목록 */
export const listMyClasses = async (): Promise<MyClass[]> =>
  (await get<MyClassOut[]>('/me/classes')).map((c) => ({
    class_id: sid(c.class_id),
    class_name: c.class_name,
    alias: c.student_no,
    enrollment_status: c.enrollment_status,
    assignments: c.assignments.map(({ seq, language, ...a }) => ({ ...a, id: sid(seq), language: langToUi(language) })),
  }))
