import { useState } from 'react'

import type { GradingItem } from '../../../api/reports'
import { CodeBlock } from '../../../components/CodeBlock'

type Props = {
  item: GradingItem
  saving: boolean
  error: string | null
  onSave: (body: { score: number; feedback: string }) => void
}

/** 간단 제작 답안 하나 채점: 채점 기준 체크리스트 · 점수 · 피드백 */
export default function GradeCard({ item, saving, error, onSave }: Props) {
  const [checked, setChecked] = useState<boolean[]>(() => item.rubric.map(() => false))
  const [score, setScore] = useState(item.score === null ? '' : String(item.score))
  const [feedback, setFeedback] = useState(item.feedback)
  const graded = item.score !== null

  return (
    <div className="gq">
      <div className="spread">
        <div className="row">
          <b>{item.student_name}</b>
          <span className="chip">문항 {item.question_index + 1}</span>
          {item.signals.length > 0 && <span className="chip warn">참고 신호 {item.signals.length}</span>}
        </div>
        {graded ? <span className="chip good">{item.score} / {item.points}점 확정</span> : <span className="chip warn">채점 대기</span>}
      </div>
      <CodeBlock code={item.content} />
      {item.signals.length > 0 && (
        <p className="note">참고 신호: {item.signals.join(' · ')} — 판정이 아니라 확인이 필요하다는 표시예요. 점수는 아래 기준으로만 매겨 주세요.</p>
      )}
      <div className="stack" style={{ gap: 6 }}>
        <span className="label">채점 기준</span>
        {item.rubric.map((r, j) => (
          <label className="check" key={r}>
            <input type="checkbox" checked={checked[j]} onChange={(e) => setChecked((c) => c.map((v, k) => (k === j ? e.target.checked : v)))} />
            <span>{r}</span>
          </label>
        ))}
      </div>
      <div className="row">
        <label className="row note">
          점수
          <input className="inp pts" type="number" min={0} max={item.points} value={score} onChange={(e) => setScore(e.target.value)} />/ {item.points}점
        </label>
        <input className="inp" style={{ flex: 1, minWidth: 200 }} aria-label="피드백" placeholder="학생에게 보낼 피드백 (선택)" value={feedback} onChange={(e) => setFeedback(e.target.value)} />
        <button className="btn primary sm" disabled={saving || score === ''} onClick={() => onSave({ score: Number(score), feedback })}>
          {graded ? '다시 확정' : '점수 확정'}
        </button>
      </div>
      {error && <p className="error-text">{error}</p>}
    </div>
  )
}
