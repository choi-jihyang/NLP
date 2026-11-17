type Props = { isPending: boolean; error: Error | null }

/** 불러오는 중 · 오류 표시. 데이터가 준비되면 아무것도 그리지 않는다 */
export function QueryState({ isPending, error }: Props) {
  if (error) return <p className="error-text">불러오지 못했어요: {error.message}</p>
  if (isPending) return <p className="note">불러오는 중…</p>
  return null
}
