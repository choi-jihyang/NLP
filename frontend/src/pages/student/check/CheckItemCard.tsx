import type { CheckItem, Confidence } from '../../../api/understanding'
import { AnswerInput } from '../../../components/AnswerInput'
import { CodeBlock } from '../../../components/CodeBlock'

type Props = {
  number: number
  item: CheckItem
  value: string
  confidence: Confidence | null
  done: boolean
  onChange: (value: string) => void
  onConfidence: (value: Confidence) => void
}

const CONFIDENCE: { value: Confidence; label: string }[] = [
  { value: 'SURE', label: '확실해요' },
  { value: 'UNSURE', label: '조금 헷갈려요' },
  { value: 'DONT_KNOW', label: '모르겠어요' },
]

/** 이해 확인의 변형 문제 하나 + 자신감 선택 */
export default function CheckItemCard({ number, item, value, confidence, done, onChange, onConfidence }: Props) {
  return (
    <section className="panel stack">
      <div className="row">
        <b>{number}. 변형 문제</b>
        <span className="chip">{item.type === 'MULTIPLE_CHOICE' ? '객관식 퀴즈' : '출력 예측'}</span>
      </div>
      <p className="qtext">{item.prompt}</p>
      <CodeBlock code={item.code} />
      <AnswerInput id={`check-${item.question_id}`} type={item.type} choices={item.choices} value={value} onChange={onChange} disabled={done} />
      <div className="row">
        <span className="note">이 답에 얼마나 확신하나요?</span>
        <div className="pills" role="radiogroup" aria-label="확신 정도">
          {CONFIDENCE.map((c) => (
            <label key={c.value}>
              <input
                type="radio"
                name={`conf-${item.question_id}`}
                checked={confidence === c.value}
                disabled={done}
                onChange={() => onConfidence(c.value)}
              />
              {c.label}
            </label>
          ))}
        </div>
      </div>
    </section>
  )
}
