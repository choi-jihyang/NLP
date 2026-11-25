import { nid, post } from './client'

export type PasteField = 'ANSWER' | 'CHAT' | 'CONCEPT_CHECK'

/** 붙여넣기 기록. 내용은 보내지 않고 길이와 시점만 보낸다 (불변식 I5) */
export type PasteEvent = {
  question_id: string
  field: PasteField
  length: number
  pasted_at: string
}

export const logPaste = (event: PasteEvent) =>
  post<{ ok: boolean }>('/paste-events', { ...event, question_id: nid(event.question_id) })
