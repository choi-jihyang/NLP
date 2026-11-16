import type { ChatTurn, HelpChoice } from '../../../api/chat'
import { TracePipe } from '../../../components/TracePipe'

type Props = {
  turn: ChatTurn
  isLast: boolean
  debug: boolean
  onChoose: (choice: HelpChoice) => void
}

const CHOICES: { value: HelpChoice; title: string; desc: string }[] = [
  { value: 'FIRST_HINT', title: '첫 힌트만 받기', desc: '어디서 시작할지 알려줘요' },
  { value: 'FEEDBACK', title: '내가 짠 코드 피드백 받기', desc: '코드를 보내면 그다음 단계를 도와줘요' },
  { value: 'ORIGINAL', title: '원래 질문 그대로 보내기', desc: '교수자가 정한 범위 안에서 답해요' },
]

/** 채팅 한 줄. 완성 답안 요청이면 도움 방식을 고르게 한다 */
export default function ChatMessage({ turn, isLast, debug, onChoose }: Props) {
  if (turn.role === 'STUDENT') return <div className="m me">{turn.text}</div>
  const trace = turn.trace

  return (
    <div className="m bot">
      <div className="bubble">{turn.text}</div>
      {turn.response_mode === 'OFFER_CHOICES' && isLast && (
        <div className="pick">
          {CHOICES.map((c) => (
            <button key={c.value} onClick={() => onChoose(c.value)}>
              {c.title}
              <small>{c.desc}</small>
            </button>
          ))}
        </div>
      )}
      {debug && trace && (
        <>
          <TracePipe
            classification={trace.classification}
            attempt={trace.attempt}
            leakBlocked={trace.leak_blocked}
            externalSignals={trace.external_signals}
          />
          {trace.blocked_draft && (
            <details className="draft">
              <summary>차단된 AI 초안 보기</summary>
              <pre>{trace.blocked_draft}</pre>
              <span className="note">정답이나 그대로 제출 가능한 완성 코드가 들어 있어 학생에게 보내지 않았어요.</span>
            </details>
          )}
        </>
      )}
    </div>
  )
}
