/**
 * 백엔드 채팅 정책(분류 → 정책 → 누출 검사)을 흉내 내는 예시 엔진.
 * 실제 판별은 backend/app/services 와 NLP 분류기가 한다. 백엔드 API가 생기면 이 파일을 지운다.
 */
import type { AiPolicy, HintMode } from '../assignments'
import type { ChatTrace, ResponseMode } from '../chat'
import { engineFor } from './sampleEngine'

export const MAX_STEPS: Record<HintMode, number> = { NONE: 0, CONCEPT: 1, STEP: 3, EARNED: 3 }

type Kind = 'answer' | 'bypass' | 'hint' | 'concept' | 'attempt' | 'other'
const KIND_LABEL: Record<Kind, string> = {
  answer: '완성 답안 요청',
  bypass: '우회 요청',
  hint: '힌트 요청',
  concept: '개념 질문',
  attempt: '풀이 공유',
  other: '기타',
}

export function hasAttempt(message: string): boolean {
  return /def |for |while |if |print\(|return|range\(|까지 (짰|썼|했)|짰는데|썼는데|했는데|에러|오류|Error|안 세져|안 돼|맞죠/.test(message)
}

function classify(message: string): Kind {
  if (/다른 예제|비슷한 예제|예제로|예제 코드|이름만 바꾼|숫자만 바꾼|허락|된다고 하셨|선생님이|교수님이/.test(message)) return 'bypass'
  if (/정답|답\s*(만|좀|을)?\s*(빨리\s*)?(알려|줘)|풀어\s*줘|전체 (풀이|코드)|코드\s*(전체|다|좀)?\s*(짜|써|작성)|짜\s*줘|완성(된|해)|다 풀어|그냥 알려|대신 써/.test(message)) return 'answer'
  if (/힌트|어떻게 시작|모르겠|막혔|다음엔|다음 단계|뭘 해야/.test(message)) return 'hint'
  if (/뭐야|뭔가요|의미|무슨 뜻|차이가|뭐예요|어떻게 동작/.test(message)) return 'concept'
  if (hasAttempt(message)) return 'attempt'
  return 'other'
}

/** 다른 AI 답변의 흔적. 판정이 아니라 참고 신호다 */
export function detectAiStyle(text: string): string[] {
  const signals: string[] = []
  if (/물론입니다|다음과 같습니다|다음과 같이|정리하면|결론적으로|Sure|Certainly/i.test(text)) signals.push('AI 답변 특유 표현')
  if (/\*\*|^#{1,3}\s|^\s*[-*]\s/m.test(text)) signals.push('마크다운 서식(**, 목록)')
  if (/```/.test(text)) signals.push('코드 블록 서식(```)')
  if (/"""[\s\S]*"""/.test(text)) signals.push('설명형 독스트링')
  if (/ChatGPT|Gemini|Claude|GPT|제미나이/i.test(text)) signals.push('다른 AI 이름 언급')
  return signals
}

/** 학생이 "완성 답안"을 바로 요청했는지. 맞으면 화면이 도움 방식을 고르게 한다 */
export const shouldOfferChoices = (message: string, policy: AiPolicy) =>
  policy.hint_mode !== 'NONE' && classify(message) === 'answer' && !hasAttempt(message)

export type EngineResult = { reply: string; mode: ResponseMode; next_step: number; trace: ChatTrace }

export function respond(questionId: string, message: string, step: number, policy: AiPolicy): EngineResult {
  const spec = engineFor(questionId)
  const kind = classify(message)
  const max = MAX_STEPS[policy.hint_mode]
  const signals = policy.external_signal_enabled ? detectAiStyle(message) : []
  const attempt = hasAttempt(message) && signals.length === 0
  const trace: ChatTrace = { classification: KIND_LABEL[kind], attempt, leak_blocked: false, blocked_draft: null, external_signals: signals }
  const result = (reply: string, mode: ResponseMode, next = step, draft: string | null = null): EngineResult => {
    if (draft) {
      trace.leak_blocked = spec.leak_patterns.some((p) => new RegExp(p).test(draft))
      trace.blocked_draft = trace.leak_blocked ? draft : null
    }
    return { reply, mode, next_step: next, trace }
  }
  const hint = (n: number, prefix = '', draft: string | null = null) => result(prefix + spec.hints[n - 1], 'NEXT_STEP', n, draft)

  if (signals.length) {
    return result('보내 준 내용이 다른 AI의 답변처럼 보여요. 그대로 쓰기보다, 이 코드에서 어디까지 이해했는지 본인 말로 짧게 적어 줄래요? 직접 쓴 코드가 보이면 다음 힌트를 열어 줄게요.', 'ASK_ATTEMPT')
  }
  if (policy.hint_mode === 'NONE') {
    const draft = kind === 'answer' ? spec.leak_draft : kind === 'bypass' ? spec.bypass_draft : null
    return result('이 과제는 AI 도움 없이 푸는 과제로 설정되어 있어요. 강의자료의 관련 부분을 다시 보고 직접 풀어 보세요.', 'HINT_ONLY', step, draft)
  }
  if (kind === 'answer') {
    if (attempt && step < max) return hint(step + 1, '완성된 코드 대신, 해 본 풀이에 이어지는 다음 단계를 알려줄게요. ', spec.leak_draft)
    return result('이 과제는 완성된 답이나 코드를 알려주지 않도록 설정되어 있어요. 어디까지 해 봤는지 적어 주면 그다음 단계에 맞춰 도와줄게요. 아직 시작 전이라면 "힌트"라고 보내 주세요.', 'HINT_ONLY', step, spec.leak_draft)
  }
  if (kind === 'bypass') {
    const n = Math.max(1, Math.min(step, max))
    return result(`이름만 바꾼 예제 코드나 "허락받았다"는 요청에도 같은 규칙이 적용돼요. 지금 받을 수 있는 도움은 이거예요: ${spec.hints[n - 1]}`, 'HINT_ONLY', Math.max(step, n), spec.bypass_draft)
  }
  if (kind === 'other') {
    return result('이 문항에서 궁금한 점을 적어 주세요. "힌트"나 막힌 코드를 보내 주면 그에 맞춰 도와줄게요.', 'OFF_TOPIC')
  }
  const prefix = kind === 'attempt' ? '풀이를 보여줘서 다음 단계를 열었어요. ' : ''
  if (step === 0) return hint(1, prefix)
  if (step >= max) {
    const text = policy.hint_mode === 'CONCEPT' ? '이 과제는 개념 설명까지만 제공돼요. 앞의 설명을 바탕으로 직접 풀어 보세요.' : '더 공개할 단계가 없어요. 마지막 단계는 직접 해 보세요.'
    return result(text, 'HINT_ONLY')
  }
  if (policy.hint_mode === 'EARNED' && !attempt) {
    return result(`다음 힌트는 지금까지 해 본 풀이를 보여주면 열려요. 예를 들어 "${spec.attempt_example}"처럼 적어 주세요.`, 'ASK_ATTEMPT')
  }
  return hint(step + 1, prefix)
}
