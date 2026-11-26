import type { RunResult } from '../api/submissions'

type Props = { run: RunResult }

/** 공개 테스트 실행 결과. 표준 입력 → 기대 출력 / 실제 출력. 컴파일 오류는 한 번만 위에 보여 준다 */
export function TestResults({ run }: Props) {
  return (
    <div className="tests">
      {!run.ok && run.error && <pre className="error-text">{run.error}</pre>}
      {run.ok &&
        run.results.map((t, i) => (
          <div className="trow" key={`${t.input}-${i}`}>
            <span className={t.passed ? 'pass' : 'fail'} aria-label={t.passed ? '통과' : '실패'}>
              {t.passed ? '✓' : '✗'}
            </span>
            <code>입력 {t.input.trim() || '(없음)'}</code>
            <code>
              기대 {t.expected_output} · 결과 {t.actual_output ?? '—'}
            </code>
            {t.error && <span className="chip warn">{t.error}</span>}
            <span className="chip">공개 테스트</span>
          </div>
        ))}
    </div>
  )
}
