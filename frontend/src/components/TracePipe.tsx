type Props = {
  classification: string
  attempt: boolean
  leakBlocked: boolean
  externalSignals: string[]
  hasDraft?: boolean
}

/** 판별 과정 (요청 분류 → 시도 근거 → 누출 검사). 교수자 화면과 시연용 표시에만 쓴다 */
export function TracePipe({ classification, attempt, leakBlocked, externalSignals, hasDraft = true }: Props) {
  if (externalSignals.length) {
    return (
      <div className="pipe">
        <span className="chip acc">{classification}</span>
        <span className="arr">→</span>
        <span className="chip bad">외부 AI 참고 신호: {externalSignals.join(', ')}</span>
        <span className="arr">→</span>
        <span className="chip">시도 근거로 인정 안 함</span>
      </div>
    )
  }
  return (
    <div className="pipe">
      <span className="chip acc">{classification}</span>
      <span className="arr">→</span>
      <span className={`chip ${attempt ? 'good' : ''}`}>시도 근거 {attempt ? '있음' : '없음'}</span>
      <span className="arr">→</span>
      {!hasDraft ? (
        <span className="chip">초안 없음</span>
      ) : leakBlocked ? (
        <span className="chip bad">누출 검사: 차단 → 재작성</span>
      ) : (
        <span className="chip good">누출 검사: 통과</span>
      )}
    </div>
  )
}
