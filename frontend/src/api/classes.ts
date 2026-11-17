import type { AiPolicy, HintMode } from './assignments'
import type { PlanCode } from './plans'
import { mockClasses } from './mock/classStore'
import { mockEnrollments } from './mock/enrollmentStore'

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

export const listClasses = () => mockClasses.list()
/** 클래스 개설. 수업 코드가 새로 발급된다 */
export const createClass = (body: ClassCreate) => mockClasses.create(body)
/** 이 클래스에서 새로 만드는 과제에 미리 채울 AI 도움 정책 */
export const getAiDefaults = (classId: string) => mockClasses.aiDefaults(classId)
export const saveAiDefaults = (classId: string, policy: AiPolicy) => mockClasses.saveAiDefaults(classId, policy)
export const getClass = (classId: string) => mockClasses.get(classId)
export const listStudents = (classId: string) => mockEnrollments.students(classId)
/** 학생: 참여한 클래스와 과제 목록 */
export const listMyClasses = () => mockClasses.mine()
