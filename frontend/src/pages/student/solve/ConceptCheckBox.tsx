import { useState } from 'react'

import type { ConceptCheck, ConceptReply } from '../../../api/submissions'

type Props = {
  check: ConceptCheck
  busy: boolean
  onAnswer: (body: ConceptReply) => void
  onCancel: () => void
  onPaste: (length: number) => void
}

/**
 * 힌트 없이 처음 낸 문항: 제출 직전에 쓴 개념을 묻는다.
 * 답변에 AI 작성 신호가 높으면 서버가 질문을 하나 더 붙인다. 판정 결과는 학생에게 보여주지 않는다.
 * 질문이 바뀌면 부모가 key로 이 컴포넌트를 새로 만든다(입력·시간 초기화).
 */
export default function ConceptCheckBox({ check, busy, onAnswer, onCancel, onPaste }: Props) {
  const [reply, setReply] = useState('')
  const [startedAt] = useState(() => Date.now())
  const followUp = check.answered > 0
  const question = check.questions[check.answered]
  const tooShort = reply.trim().length < 2

  return (
    <div className="boxed">
      <div className="row">
        <b>제출 전 개념 확인</b>
        <span className="chip acc">{followUp ? '질문 하나 더' : '혼자 푼 문항'}</span>
      </div>
      <div className="m bot" style={{ maxWidth: '100%' }}>
        <div className="bubble">
          {followUp ? '고마워요. 하나만 더 물어볼게요. ' : '힌트 없이 풀었네요. 제출하기 전에 하나만 물어볼게요. '}
          {question}
        </div>
      </div>
      <textarea
        className="inp"
        aria-label="개념 확인 답변"
        placeholder="한두 문장으로 본인 말로 적어 주세요"
        value={reply}
        onChange={(e) => setReply(e.target.value)}
        onPaste={(e) => onPaste(e.clipboardData.getData('text').length)}
      />
      <div className="row">
        <button
          className="btn primary"
          disabled={busy || tooShort}
          onClick={() => onAnswer({ reply: reply.trim(), elapsed_ms: Date.now() - startedAt })}
        >
          답하고 제출
        </button>
        {!followUp && (
          <button className="btn" disabled={busy} onClick={onCancel}>답 고치러 돌아가기</button>
        )}
      </div>
      <p className="note">이 답변은 점수에 들어가지 않아요. 짧아도 괜찮으니 본인 말로 적어 주세요.</p>
    </div>
  )
}
