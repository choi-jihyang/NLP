import type { Question } from '../../../../api/assignments'
import { CIRCLED } from '../../../../components/choiceLabel'

type Props = { index: number; question: Question; onChange: (patch: Partial<Question>) => void }

/** 객관식: 선택지 · 정답 · 오답별 예상 오개념 */
export default function ChoiceEditor({ index, question: q, onChange }: Props) {
  const setChoice = (j: number, value: string) => onChange({ choices: q.choices.map((c, k) => (k === j ? value : c)) })
  const setMis = (j: number, value: string) => onChange({ misconceptions: { ...q.misconceptions, [String(j)]: value } })

  return (
    <div className="stack" style={{ gap: 8 }}>
      <span className="label">선택지와 정답 · 왼쪽 동그라미로 정답을 지정하고, 오답에는 예상 오개념을 적어 두면 리포트에 집계돼요</span>
      {q.choices.map((c, j) => {
        const correct = q.answer === String(j)
        return (
          <div key={j} className="stack" style={{ gap: 4 }}>
            <div className="chinp">
              <input
                type="radio"
                name={`answer-${index}`}
                checked={correct}
                aria-label={`${CIRCLED[j]} 정답으로 지정`}
                onChange={() => onChange({ answer: String(j) })}
              />
              <input className="inp mono" value={c} placeholder={`${CIRCLED[j]} 선택지`} onChange={(e) => setChoice(j, e.target.value)} />
            </div>
            {!correct && (
              <input
                className="inp"
                style={{ marginLeft: 36, width: 'calc(100% - 36px)', fontSize: '0.85rem' }}
                value={q.misconceptions[String(j)] ?? ''}
                placeholder="이 선택지를 고르는 학생의 예상 오개념 (선택)"
                onChange={(e) => setMis(j, e.target.value)}
              />
            )}
          </div>
        )
      })}
      {q.choices.length < 6 && (
        <div>
          <button className="btn sm" onClick={() => onChange({ choices: [...q.choices, ''] })}>+ 선택지 추가</button>
        </div>
      )}
    </div>
  )
}
