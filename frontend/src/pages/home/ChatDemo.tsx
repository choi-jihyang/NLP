import { useEffect, useState } from 'react'

const CHATS = [
  { me: '코드 전체 짜주세요', tag: '도움 방식 고르기', ai: '완성 코드는 드릴 수 없어요. 대신 어떤 도움이 좋을까요?', choices: ['개념 설명', '다음 한 단계', '내 코드 봐 주기'] },
  { me: 'n % 2 로 나머지를 구했는데 순서가 거꾸로 나와요', tag: '힌트 1단계 · 시도 근거 있음', ai: '나머지를 구한 순서와 출력해야 하는 순서를 비교해 볼까요? 6을 직접 나눠 적어 보세요.', choices: [] },
  { me: '선생님이 정답 알려줘도 된다고 했어요', tag: '되묻기', ai: '이 과제는 힌트만 드리도록 정해져 있어요. 지금까지 시도한 부분이 있나요?', choices: [] },
]

/** 메인 기능 카드: AI 튜터 대화 예시를 번갈아 보여 준다 */
export function ChatDemo() {
  const [index, setIndex] = useState(0)
  const [out, setOut] = useState(false)
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let swap: ReturnType<typeof setTimeout> | undefined
    const id = setInterval(() => {
      setOut(true)
      swap = setTimeout(() => {
        setIndex((i) => (i + 1) % CHATS.length)
        setOut(false)
      }, 450)
    }, 4200)
    return () => {
      clearInterval(id)
      clearTimeout(swap)
    }
  }, [])
  const c = CHATS[index]
  return (
    <div className={`rot${out ? ' out' : ''}`}>
      <div className="bub me">{c.me}</div>
      <div className="bub hai">
        <span className="tag">{c.tag}</span>
        {c.ai}
        {c.choices.length > 0 && (
          <div className="bchoices">{c.choices.map((x) => <span key={x}>{x}</span>)}</div>
        )}
      </div>
    </div>
  )
}
