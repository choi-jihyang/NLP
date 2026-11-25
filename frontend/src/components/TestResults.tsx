import type { TestResult } from '../api/submissions'

type Props = { results: TestResult[] }

/** 테스트 실행 결과 목록. 표준 입력 → 기대 출력 / 실제 출력. 컴파일 오류는 한 번만 위에 보여 준다 */
export function TestResults({ results }: Props) {
  const compileError = results.find((t) => t.error?.startsWith('컴파일 오류'))?.error
  return (
    <div className="tests">
      {compileError && <pre className="error-text">{compileError}</pre>}
      {results.map((t, i) => (
        <div className="trow" key={`${t.call}-${i}`}>
          <span className={t.passed ? 'pass' : 'fail'} aria-label={t.passed ? '통과' : '실패'}>
            {t.passed ? '✓' : '✗'}
          </span>
          <code>입력 {t.call.trim() || '(없음)'}</code>
          <code>
            기대 {t.expected} · 결과 {compileError ? '—' : t.actual}
          </code>
          {t.error && !compileError && <span className="chip warn">{t.error}</span>}
          <span className="chip">{t.hidden ? '숨김 테스트' : '공개 테스트'}</span>
        </div>
      ))}
    </div>
  )
}
