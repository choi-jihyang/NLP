import type { AssignmentReport } from '../../../api/reports'

type Props = { mistakes: AssignmentReport['mistakes']; supplement: AssignmentReport['supplement'] }

const KIND_LABEL = { CHOICE: '객관식 선택 비율', ANSWER: '자주 나온 오답', TEST: '자주 실패한 테스트' } as const

/** 반 전체가 틀린 지점 + 다음 수업 보충 제안 */
export default function MistakeSection({ mistakes, supplement }: Props) {
  return (
    <>
      <section className="panel sec">
        <h3>반 전체가 틀린 지점</h3>
        <div className="two">
          {mistakes.map((m) => {
            const wrong = m.rows.filter((r) => !r.correct)
            const top = wrong.reduce((a, b) => (b.rate > a.rate ? b : a), wrong[0])
            return (
              <div className="stack" style={{ gap: 10 }} key={m.question_index}>
                <b>
                  문항 {m.question_index + 1} <span className="note">· {KIND_LABEL[m.kind]}</span>
                </b>
                {m.rows.map((r) => (
                  <div className="drow" key={r.label}>
                    <span className="mono">{r.label}</span>
                    <div className="bar">
                      <i className={r.correct ? 'correct' : r === top ? 'top' : ''} style={{ width: `${r.rate}%` }} />
                    </div>
                    <span className="rate">{r.rate}%</span>
                    {r.note && <em>{r.note}</em>}
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      </section>
      {supplement && (
        <section className="panel sec">
          <div className="spread">
            <h3>다음 수업 보충 제안</h3>
            <span className="chip bad">
              문항 {supplement.question_index + 1} · {supplement.rate}%가 같은 오답
            </span>
          </div>
          <p>{supplement.summary} 아래 보충 문항은 교수자가 검토한 뒤 배포돼요.</p>
          <ol className="sup mono">
            {supplement.items.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ol>
        </section>
      )}
    </>
  )
}
