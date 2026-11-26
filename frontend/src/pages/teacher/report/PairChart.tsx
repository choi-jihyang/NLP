import type { QuestionStat } from '../../../api/reports'

type Props = { stats: QuestionStat[] }

/** AI와 함께(원문제) vs 혼자서(확인 문제) 정답률 막대 */
export default function PairChart({ stats }: Props) {
  return (
    <section className="panel sec">
      <div className="spread">
        <h3>AI와 함께 vs 혼자서</h3>
        <div className="legend">
          <span>
            <i className="with-ai" />원문제 (AI 도움 가능)
          </span>
          <span>
            <i className="alone" />확인 문제 (AI 없음)
          </span>
        </div>
      </div>
      {stats.map((s) => (
        <div className="pair" key={s.question_index}>
          <div>
            <b>문항 {s.question_index + 1}</b>
            <div className="note">힌트 평균 {s.avg_hint_steps}단계</div>
          </div>
          <div className="stack" style={{ gap: 5 }}>
            <div className="barrow" aria-label={`원문제 정답률 ${s.correct_rate}%`}>
              <div className="bar">
                <i className="with-ai" style={{ width: `${s.correct_rate}%` }} />
              </div>
              <span>{s.correct_rate}%</span>
            </div>
            {s.variant_rate === null ? (
              <div className="barrow" aria-label="확인 문제 없음">
                <span className="note">확인 문제 없음</span>
              </div>
            ) : (
              <div className="barrow" aria-label={`확인 문제 정답률 ${s.variant_rate}%`}>
                <div className="bar">
                  <i className="alone" style={{ width: `${s.variant_rate}%` }} />
                </div>
                <span>{s.variant_rate}%</span>
              </div>
            )}
          </div>
        </div>
      ))}
      <p className="note">차이가 큰 문항일수록 학생들이 힌트로 풀었지만 방법을 아직 익히지 못했을 가능성이 높아요.</p>
    </section>
  )
}
