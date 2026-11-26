import { get, post } from './client'

/** schema.md 의 ResponseMode + 도움 방식 고르기(OFFER_CHOICES) */
export type ResponseMode = 'NEXT_STEP' | 'HINT_ONLY' | 'ASK_ATTEMPT' | 'OFF_TOPIC' | 'USAGE_LIMIT' | 'OFFER_CHOICES'

/** 완성 답안을 바로 요청했을 때 학생이 고르는 도움 방식 */
export type HelpChoice = 'FIRST_HINT' | 'FEEDBACK' | 'ORIGINAL'

/** 판별 과정. 시연용으로만 보여 주고 실제 학생 화면에는 없다 */
export type ChatTrace = {
  classification: string
  attempt: boolean
  leak_blocked: boolean
  blocked_draft: string | null
  external_signals: string[]
}

export type ChatTurn = {
  role: 'STUDENT' | 'ASSISTANT'
  text: string
  response_mode: ResponseMode | null
  trace: ChatTrace | null
}

export type ChatState = {
  question_id: number
  turns: ChatTurn[]
  hint_step: number
  max_hint_steps: number
  usage_remaining: number
}

/** 붙여넣기 여부는 싣지 않는다 — /paste-events(field = CHAT)로 따로(불변식 I5) */
export type ChatRequest = {
  assignment_id: number
  question_id: number
  message: string
  choice?: HelpChoice
}

const url = (a: number, q: number) => `/assignments/${a}/questions/${q}/chat`

export const getChat = (assignmentId: number, questionId: number) => get<ChatState>(url(assignmentId, questionId))
export const sendChat = ({ assignment_id, question_id, message, choice }: ChatRequest) =>
  post<ChatState>(url(assignment_id, question_id), choice ? { message, choice } : { message })
