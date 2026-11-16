import type { Question, TestCase } from '../../../../api/assignments'

type Props = { question: Question; onChange: (patch: Partial<Question>) => void }

/** 코드 작성: 시작 코드와 테스트 케이스(공개·숨김) */
export default function CodeTestsEditor({ question: q, onChange }: Props) {
  const setTest = (j: number, patch: Partial<TestCase>) => onChange({ tests: q.tests.map((t, k) => (k === j ? { ...t, ...patch } : t)) })

  return (
    <>
      <label className="field">
        <span className="label">학생에게 주는 시작 코드</span>
        <textarea className="code" style={{ minHeight: 110 }} spellCheck={false} value={q.starter_code} onChange={(e) => onChange({ starter_code: e.target.value })} />
      </label>
      <div className="stack" style={{ gap: 8 }}>
        <span className="label">테스트 케이스 · 숨김 테스트는 학생에게 입력이 보이지 않아요</span>
        {q.tests.map((t, j) => (
          <div className="tedit" key={j}>
            <input className="inp mono" aria-label={`테스트 ${j + 1} 호출`} value={t.call} placeholder="호출 예: f([1, 2])" onChange={(e) => setTest(j, { call: e.target.value })} />
            <input className="inp mono" aria-label={`테스트 ${j + 1} 기대 출력`} value={t.expected} placeholder="기대 출력" onChange={(e) => setTest(j, { expected: e.target.value })} />
            <label className="check note">
              <input type="checkbox" checked={t.hidden} onChange={(e) => setTest(j, { hidden: e.target.checked })} />
              숨김
            </label>
            <button className="x" aria-label={`테스트 ${j + 1} 삭제`} onClick={() => onChange({ tests: q.tests.filter((_, k) => k !== j) })}>
              ×
            </button>
          </div>
        ))}
        <div>
          <button className="btn sm" onClick={() => onChange({ tests: [...q.tests, { call: '', expected: '', hidden: false }] })}>+ 테스트 추가</button>
        </div>
      </div>
      <p className="note">제출하면 테스트를 실행해서 모두 통과하면 정답으로 채점해요. 학생은 제출 전에 공개 테스트만 실행해 볼 수 있어요.</p>
    </>
  )
}
