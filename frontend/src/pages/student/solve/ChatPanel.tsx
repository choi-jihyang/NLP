import { useEffect, useRef, useState, type FormEvent } from 'react'

import type { ChatState, HelpChoice } from '../../../api/chat'
import ChatMessage from './ChatMessage'

type Props = {
  index: number
  chat: ChatState | undefined
  modeLabel: string
  earned: boolean
  /** 잠금 사유. 있으면 입력을 막고 안내를 보여 준다 */
  lock: { title: string; note: string } | null
  sending: boolean
  debug: boolean
  onSend: (body: { message: string; choice?: HelpChoice; pasted?: boolean }) => void
  onPaste: (length: number) => void
}

const QUICK = ['첫 힌트 주세요', '여기까지 짰는데 다음 줄을 모르겠어요']
const BYPASS_EXAMPLES = ['코드 전체 짜주세요', '함수 이름만 바꾼 예제 코드로 보여줘']

/** 오른쪽 학습 AI 채팅 패널 */
export default function ChatPanel({ index, chat, modeLabel, earned, lock, sending, debug, onSend, onPaste }: Props) {
  const [text, setText] = useState('')
  const [pasted, setPasted] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const turns = chat?.turns ?? []
  const max = chat?.max_hint_steps ?? 0
  const step = chat?.hint_step ?? 0

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [turns.length])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    onSend({ message: text.trim(), pasted })
    setText('')
    setPasted(false)
  }
  const quick = debug ? [...QUICK, ...BYPASS_EXAMPLES] : QUICK

  return (
    <section className="panel ai" aria-label="학습 AI">
      <div className="ai-h">
        <div className="spread">
          <b>AI 도움 · 문항 {index + 1}</b>
          <span className="chip acc">{modeLabel}</span>
        </div>
        {max > 0 ? (
          <>
            <div className="lv">
              {Array.from({ length: max }, (_, i) => (
                <i key={i} className={i < step ? 'on' : ''} />
              ))}
            </div>
            <span className="note">
              열린 힌트 {step} / {max}단계{earned && ' · 내 코드를 보여주면 다음 단계가 열려요'}
            </span>
          </>
        ) : (
          <span className="note">이 과제는 AI 도움 없이 풀어요.</span>
        )}
      </div>
      <div className="msgs" ref={listRef}>
        {turns.length ? (
          turns.map((t, i) => (
            <ChatMessage key={i} turn={t} isLast={i === turns.length - 1} debug={debug} onChoose={(choice) => onSend({ message: '', choice })} />
          ))
        ) : lock ? null : (
          <p className="empty">막히면 질문해 보세요. 에러 메시지나 막힌 줄을 붙여 주면, 완성 코드 대신 다음 한 단계를 함께 찾아요.</p>
        )}
      </div>
      <div className="quick">
        {quick.map((q) => (
          <button key={q} disabled={sending || !!lock} onClick={() => onSend({ message: q })}>
            {q}
          </button>
        ))}
      </div>
      <form className="send" onSubmit={handleSubmit}>
        <input
          className="inp"
          aria-label="학습 AI에게 보낼 메시지"
          placeholder="질문하거나 막힌 코드·에러 메시지를 적어 주세요"
          autoComplete="off"
          value={text}
          disabled={!!lock}
          onChange={(e) => setText(e.target.value)}
          onPaste={(e) => {
            setPasted(true)
            onPaste(e.clipboardData.getData('text').length)
          }}
        />
        <button className="btn primary" disabled={sending || !!lock || !text.trim()}>보내기</button>
      </form>
      {lock && (
        <div className="lock">
          <b>{lock.title}</b>
          <span className="note">{lock.note}</span>
        </div>
      )}
    </section>
  )
}
