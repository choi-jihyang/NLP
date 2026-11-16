type Props = { code: string }

/** 문제 코드·요구사항을 보여 주는 어두운 코드 상자. 빈 문자열이면 그리지 않는다 */
export function CodeBlock({ code }: Props) {
  if (!code) return null
  return <pre className="snip">{code}</pre>
}
