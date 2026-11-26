import type { Question, SimulationCase } from '../../../api/assignments'
import { TracePipe } from '../../../components/TracePipe'
import { TYPE_LABEL } from './questionText'

type Props = { cases: SimulationCase[]; questions: Question[]; custom: boolean }

/** "학생처럼 졸라보기" 결과 */
export default function SimulationList({ cases, questions, custom }: Props) {
  if (!cases.length) return <p className="note">AI 도움을 받을 수 있는 문항이 없어요.</p>
  const blocked = cases.filter((c) => c.leak_blocked).length
  const signals = cases.filter((c) => c.external_signals.length).length

  return (
    <div className="stack">
      {cases.map((c, i) => {
        const q = questions[c.question_index]
        return (
          <div className="case" key={i}>
            <div className="spread">
              <span className="say">{c.message}</span>
              <span className="chip">
                문항 {c.question_index + 1}
                {q && ` · ${TYPE_LABEL[q.type]}`}
              </span>
            </div>
            <TracePipe classification={c.classification} attempt={c.attempt} leakBlocked={c.leak_blocked} externalSignals={c.external_signals} />
            <div className="reply">{c.reply}</div>
          </div>
        )
      })}
      <p className="note">
        {blocked}개의 답변 초안이 정답이나 완성 코드를 담고 있어 차단되었고, {signals}개의 메시지에서 외부 AI 의심 신호가 잡혔어요. 정상적인 힌트 요청은 그대로 전달됐어요.
        {custom && ' 직접 쓴 지시문이 적용된 결과예요(고정 규칙 · 누출 검사는 그대로).'}
      </p>
    </div>
  )
}
