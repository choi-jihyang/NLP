import { get, nid, post, sid } from './client'

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

type CheckOut = Omit<UnderstandingCheck, 'items'> & {
  items: (Omit<CheckItem, 'question_id'> & { question_id: number })[]
  submitted: boolean
}

/** 최종 제출 뒤에만. 확인 문제의 정답은 오지 않는다 */
export const getUnderstandingCheck = async (assignmentId: string): Promise<UnderstandingCheck> => {
  const r = await get<CheckOut>(`/assignments/${nid(assignmentId)}/understanding-check`)
  return { ...r, items: r.items.map((i) => ({ ...i, question_id: sid(i.question_id) })) }
}
/** 한 번만 낼 수 있다. 정오는 결과 공개 뒤 내 리포트에서만 보인다 */
export const submitUnderstandingCheck = (assignmentId: string, body: CheckSubmission) =>
  post<CheckReceipt>(`/assignments/${nid(assignmentId)}/understanding-check`, {
    explanation: body.explanation,
    answers: body.answers.map((a) => ({ ...a, question_id: nid(a.question_id) })),
  })
