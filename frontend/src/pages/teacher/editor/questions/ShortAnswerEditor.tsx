import type { Question } from '../../../../api/assignments'

type Props = { question: Question; onChange: (patch: Partial<Question>) => void }

/** 출력 예측: 정답과 함께 정답으로 볼 표기 */
export default function ShortAnswerEditor({ question: q, onChange }: Props) {
  return (
    <>
      <div className="grid3">
        <label className="field">
          <span className="label">정답 (출력값)</span>
          <input className="inp mono" value={q.answer} onChange={(e) => onChange({ answer: e.target.value })} />
        </label>
        <label className="field">
          <span className="label">함께 정답으로 볼 표기 (쉼표로 구분)</span>
          <input
            className="inp mono"
            value={q.accepted_answers.join(', ')}
            onChange={(e) => onChange({ accepted_answers: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) })}
          />
        </label>
      </div>
      <p className="note">앞뒤 공백과 대소문자 차이는 같은 답으로 봐요.</p>
    </>
  )
}
