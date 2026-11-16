import type { QuestionType } from '../api/assignments'

import { CIRCLED } from './choiceLabel'
import { CodeEditor } from './CodeEditor'

type Props = {
  id: string
  type: QuestionType
  choices: string[]
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  onPaste?: (length: number) => void
}


/** 문항 유형에 맞는 답 입력 (객관식 선택지 · 단답 · 코드) */
export function AnswerInput({ id, type, choices, value, onChange, disabled, onPaste }: Props) {
  if (type === 'MULTIPLE_CHOICE') {
    return (
      <div className="choices" role="radiogroup">
        {choices.map((c, i) => (
          <label className="choice" key={c + i}>
            <input
              type="radio"
              name={id}
              value={String(i)}
              checked={value === String(i)}
              disabled={disabled}
              onChange={() => onChange(String(i))}
            />
            <span className="mono">
              {CIRCLED[i]} {c}
            </span>
          </label>
        ))}
      </div>
    )
  }
  if (type === 'SHORT_ANSWER') {
    return (
      <input
        id={id}
        className="inp mono"
        placeholder="답을 입력하세요"
        aria-label="답"
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        onPaste={(e) => onPaste?.(e.clipboardData.getData('text').length)}
      />
    )
  }
  return <CodeEditor id={id} value={value} onChange={onChange} disabled={disabled} onPaste={onPaste} />
}
