import type { TestResult } from '../api/submissions'

type Props = { results: TestResult[] }

/** 테스트 실행 결과 목록 */
export function TestResults({ results }: Props) {
  return (
    <div className="tests">
      {results.map((t, i) => (
        <div className="trow" key={`${t.call}-${i}`}>
          <span className={t.passed ? 'pass' : 'fail'} aria-label={t.passed ? '통과' : '실패'}>
            {t.passed ? '✓' : '✗'}
          </span>
          <code>{t.call}</code>
          <code>
            기대 {t.expected} · 결과 {t.actual}
          </code>
          <span className="chip">{t.hidden ? '숨김 테스트' : '공개 테스트'}</span>
        </div>
      ))}
    </div>
  )
}
