import { Link } from 'react-router-dom'

import type { DependencyRow, SignalRow } from '../../../api/reports'
import { SignalLevel } from '../../../components/SignalLevel'

type Props = { dependency: DependencyRow[] | null; signals: SignalRow[] | null; recordPath: (studentId: string) => string }

/** 의존 위험 학생 · 외부 AI 참고 신호 표 */
export default function StudentTables({ dependency, signals, recordPath }: Props) {
  return (
    <>
      {dependency && (
        <section className="panel sec">
          <div className="spread">
            <h3>AI로는 풀었지만 혼자서는 못 푼 학생</h3>
            <span className="chip warn">{dependency.length}명</span>
          </div>
          <p className="note">원문제는 힌트를 받아 맞혔지만, AI 없는 확인 문제는 틀린 학생이에요. 개별 확인이 필요할 수 있어요.</p>
          <div className="tbl">
            <table>
              <thead>
                <tr><th>학생</th><th>문항</th><th>원문제</th><th>받은 힌트</th><th>확인 문제 답</th><th>예상 원인</th></tr>
              </thead>
              <tbody>
                {dependency.map((d) => (
                  <tr key={`${d.student_id}-${d.question_index}`}>
                    <td><Link to={recordPath(d.student_id)}>{d.student_name}</Link></td>
                    <td className="num">{d.question_index + 1}</td>
                    <td><span className="chip good">정답</span></td>
                    <td className="num">{d.hint_steps}단계</td>
                    <td className="mono">{d.variant_answer}</td>
                    <td>{d.cause}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
      {signals && (
        <section className="panel sec">
          <div className="spread">
            <h3>외부 AI 사용 의심 신호</h3>
            <span className="chip warn">실험 기능</span>
          </div>
          <p className="note">여러 신호가 겹칠수록 강하게 표시돼요. 판정이 아니라 확인이 필요하다는 표시이고 점수에는 반영되지 않아요. 학생과 대화로 확인한 뒤 판단해 주세요.</p>
          <div className="tbl">
            <table>
              <thead>
                <tr><th>학생</th><th>문항</th><th>신호</th><th>강도</th></tr>
              </thead>
              <tbody>
                {signals.map((s) => (
                  <tr key={`${s.student_id}-${s.question_index}`}>
                    <td><Link to={recordPath(s.student_id)}>{s.student_name}</Link></td>
                    <td className="num">{s.question_index + 1}</td>
                    <td>
                      <div className="pills">
                        {s.signals.map((x) => (
                          <span className="chip" key={x}>{x}</span>
                        ))}
                      </div>
                    </td>
                    <td><SignalLevel count={s.signals.length} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  )
}
