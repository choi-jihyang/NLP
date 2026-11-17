import { mockReports } from './mock/reportStore'

/** 과제를 다 낸 뒤 AI 없이 보는 이해 확인 (내 코드 설명 + 변형 문제 + 자신감 체크) */
export type CheckItem = {
  question_id: string
  type: 'MULTIPLE_CHOICE' | 'SHORT_ANSWER'
  prompt: string
  code: string
  choices: string[]
}

export type UnderstandingCheck = {
  explain_prompt: string
  explain_code: string
  items: CheckItem[]
}

export type Confidence = 'SURE' | 'UNSURE' | 'DONT_KNOW'

export type CheckSubmission = {
  explanation: string
  answers: { question_id: string; value: string; confidence: Confidence | null }[]
}

/** 이해 확인 결과(정오·착각 주의)는 결과 공개 뒤 내 리포트에서만 보인다 */
export type CheckReceipt = { submitted_at: string }

export const getUnderstandingCheck = (assignmentId: string) => mockReports.check(assignmentId)
export const submitUnderstandingCheck = (assignmentId: string, body: CheckSubmission) =>
  mockReports.submitCheck(assignmentId, body)
