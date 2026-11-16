type Props = { count: number }

/** 외부 AI 참고 신호 개수 → 강도 칩. 판정이 아니라 확인이 필요하다는 표시 */
export function SignalLevel({ count }: Props) {
  const [label, tone] = count >= 3 ? ['높음', 'bad'] : count === 2 ? ['중간', 'warn'] : ['낮음', '']
  return <span className={`chip ${tone}`}>{label}</span>
}
