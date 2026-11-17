/**
 * 개념 확인 답변의 AI 작성 신호 (규칙 기반 자리표시).
 * 실제로는 NLP 팀의 학생 입력 분석 모델이 점수를 내고, 백엔드는 그 결과만 쓴다.
 */
import { detectAiStyle } from './chatEngine'

export type ReplyContext = { reply: string; pasted: boolean; elapsed_ms: number }

export function aiWritingSignals({ reply, pasted, elapsed_ms }: ReplyContext): string[] {
  const text = reply.trim()
  const signals = detectAiStyle(text)
  if (pasted) signals.push('답변 붙여넣기')
  if ((text.match(/(습니다|됩니다|입니다)[.!]?/g) ?? []).length >= 2) signals.push('설명문 말투(~습니다)')
  if (text.length > 250) signals.push('질문에 비해 지나치게 긴 답변')
  if (text.length > 80 && elapsed_ms < 10_000) signals.push('입력 시간에 비해 긴 답변')
  return signals
}

/** 신호가 2개 이상이면 높음으로 보고 질문을 하나 더 한다 */
export const isHighSignal = (signals: string[]) => signals.length >= 2

/** 설명에 핵심 개념어가 들어 있는지 (교수자 리포트의 "설명 충분/부족") */
export const mentionsConcept = (keywords: string[], reply: string) => keywords.some((k) => reply.replace(/\s+/g, '').includes(k.replace(/\s+/g, '')))
