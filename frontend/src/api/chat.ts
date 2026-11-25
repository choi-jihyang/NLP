import { get, nid, post } from './client'
import { logPaste } from './pasteEvents'

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
  question_id: string
  turns: ChatTurn[]
  hint_step: number
  max_hint_steps: number
  usage_remaining: number
}

export type ChatRequest = {
  assignment_id: string
  question_id: string
  message: string
  choice?: HelpChoice
  pasted?: boolean
}

type ChatStateOut = Omit<ChatState, 'question_id'> & { question_id: number }
const toState = (s: ChatStateOut): ChatState => ({ ...s, question_id: String(s.question_id) })
const url = (a: string, q: string) => `/assignments/${nid(a)}/questions/${nid(q)}/chat`

export const getChat = async (assignmentId: string, questionId: string) =>
  toState(await get<ChatStateOut>(url(assignmentId, questionId)))
/** 붙여넣기 여부는 본문에 싣지 않고 /paste-events(길이 · 시점만)로 따로 보낸다(불변식 I5) */
export const sendChat = async (req: ChatRequest) => {
  if (req.pasted) {
    await logPaste({ question_id: req.question_id, field: 'CHAT', length: req.message.length, pasted_at: new Date().toISOString() })
  }
  const body = req.choice ? { message: req.message, choice: req.choice } : { message: req.message }
  return toState(await post<ChatStateOut>(url(req.assignment_id, req.question_id), body))
}
