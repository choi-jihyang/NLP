import type { RunResult } from '../api/submissions'

type Props = { run: RunResult }

/** 공개 테스트 실행 결과 표. 표준 입력 → 기대 출력 / 내 출력. 컴파일 오류는 한 번만 위에 보여 준다 */
export function TestResults({ run }: Props) {
  const passed = run.results.filter((t) => t.passed).length
  return (
    <div className="ttable">
      <div className="th">
        <span>공개 테스트</span>
        {run.ok && <span className={`chip ${passed === run.results.length ? 'good' : 'warn'}`}>{passed} / {run.results.length} 통과</span>}
      </div>
      {!run.ok && run.error && <pre className="error-text ttable-err">{run.error}</pre>}
      {run.ok && (
        <>
          <div className="tr h"><span /><span>입력</span><span>기대 출력</span><span>내 출력</span></div>
          {run.results.map((t, i) => (
            <div className="tr" key={`${t.input}-${i}`}>
              <span className={t.passed ? 'pass' : 'fail'} aria-label={t.passed ? '통과' : '실패'}>{t.passed ? '✓' : '✗'}</span>
              <code>{t.input.trim() || '(없음)'}</code>
              <code>{t.expected_output}</code>
              <code>{t.actual_output ?? '—'}{t.error && <span className="chip warn" style={{ marginLeft: 6 }}>{t.error}</span>}</code>
            </div>
          ))}
        </>
      )}
    </div>
  )
}
