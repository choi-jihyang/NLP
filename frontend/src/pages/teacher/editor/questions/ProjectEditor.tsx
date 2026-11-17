import type { Question } from '../../../../api/assignments'

type Props = { question: Question; onChange: (patch: Partial<Question>) => void }

/** 간단 제작: 채점 기준 · 예시 코드 · AI 도움 여부 */
export default function ProjectEditor({ question: q, onChange }: Props) {
  const setRubric = (j: number, value: string) => onChange({ rubric: q.rubric.map((r, k) => (k === j ? value : r)) })

  return (
    <>
      <label className="check">
        <input type="checkbox" checked={q.ai_help} onChange={(e) => onChange({ ai_help: e.target.checked })} />
        <span>
          AI 도움 열기 · 구조 설계와 학생 코드 피드백만 하고, 요구사항 하나를 통째로 구현해 주는 답변은 누출로 보고 막아요.
        </span>
      </label>
      <div className="stack" style={{ gap: 8 }}>
        <span className="label">채점 기준 · 요구사항별로 적어 두면 채점할 때 체크리스트로 보여요</span>
        {q.rubric.map((r, j) => (
          <div className="lineedit" key={j}>
            <input className="inp" aria-label={`채점 기준 ${j + 1}`} value={r} placeholder="채점 기준" onChange={(e) => setRubric(j, e.target.value)} />
            <button className="x" aria-label={`채점 기준 ${j + 1} 삭제`} onClick={() => onChange({ rubric: q.rubric.filter((_, k) => k !== j) })}>
              ×
            </button>
          </div>
        ))}
        <div>
          <button className="btn sm" onClick={() => onChange({ rubric: [...q.rubric, ''] })}>+ 기준 추가</button>
        </div>
      </div>
      <label className="field">
        <span className="label">예시 코드 · 학생에게 공개되지 않고 누출 검사 기준으로 쓰여요 (선택)</span>
        <textarea className="code" spellCheck={false} value={q.model_answer} onChange={(e) => onChange({ model_answer: e.target.value })} />
      </label>
    </>
  )
}
