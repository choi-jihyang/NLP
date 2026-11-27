import { useState } from 'react'
import { Link } from 'react-router-dom'

type Props = {
  assignmentId: number
  submitted: number
  total: number
  finalized: boolean
  busy: boolean
  onFinalize: () => void
}

/** 아래 진행 막대: 제출한 문항 수 · 최종 제출 · 이해 확인으로 이동 */
export default function FinalizeBar({ assignmentId, submitted, total, finalized, busy, onFinalize }: Props) {
  const [confirming, setConfirming] = useState(false)
  const allDone = submitted === total

  if (finalized) {
    return (
      <div className="panel spread foot-bar">
        <span className="note">최종 제출했어요. 결과는 교수자가 공개하면 볼 수 있어요.</span>
        <Link className="btn primary" to={`/student/assignments/${assignmentId}/check`}>이해 확인으로 →</Link>
      </div>
    )
  }
  if (confirming) {
    return (
      <div className="panel boxed foot-bar">
        <b>최종 제출할까요?</b>
        <span className="note">최종 제출하면 답을 더 고칠 수 없고 AI 도움도 닫혀요. 이어서 AI 없이 짧은 이해 확인(3~5분)을 해요.</span>
        <div className="row">
          <button className="btn primary" disabled={busy} onClick={onFinalize}>최종 제출</button>
          <button className="btn" disabled={busy} onClick={() => setConfirming(false)}>더 고칠래요</button>
        </div>
      </div>
    )
  }
  return (
    <div className="panel spread foot-bar">
      <span className="note">
        {submitted} / {total}문항 제출 · 마감 전까지 고쳐서 다시 낼 수 있어요
      </span>
      {allDone ? (
        <button className="btn primary" onClick={() => setConfirming(true)}>최종 제출</button>
      ) : (
        <span className="note">모든 문항을 내면 최종 제출할 수 있어요.</span>
      )}
    </div>
  )
}
