/** 예시 채점 (정답 대조, 가짜 테스트 실행). 실제로는 백엔드가 채점한다 */
import type { Question, TestCase, Variant } from '../assignments'
import type { TestResult } from '../submissions'
import { engineFor } from './sampleEngine'

const normalize = (s: string) => s.trim().toLowerCase().replace(/\s+/g, '').replace(/^['"]|['"]$/g, '')

export function isAnswerCorrect(spec: Pick<Question | Variant, 'type' | 'answer' | 'accepted_answers'>, value: string): boolean {
  if (spec.type === 'MULTIPLE_CHOICE') return value === spec.answer
  const accepted = spec.accepted_answers.length ? spec.accepted_answers : [spec.answer]
  return accepted.some((a) => normalize(a) === normalize(value))
}

/** 코드를 실제로 실행하지 않고, 핵심 패턴이 있는지로 결과를 흉내 낸다 */
export function runTests(question: Question, code: string, includeHidden: boolean): TestResult[] {
  const patterns = engineFor(question.id).pass_patterns
  const full = patterns.length > 0 && patterns.every((p) => new RegExp(p).test(code))
  const partial = /def\s+\w+/.test(code) && /return/.test(code)
  return question.tests
    .filter((t: TestCase) => includeHidden || !t.hidden)
    .map((t, i) => {
      const passed = full || (partial && i === 0)
      return {
        call: t.call,
        expected: t.expected,
        actual: passed ? t.expected : partial ? 'None' : '오류',
        passed,
        hidden: t.hidden,
      }
    })
}
