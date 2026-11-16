import type { PendingRequest } from '../../../api/enrollments'

type Props = {
  requests: PendingRequest[]
  busyId: string | null
  onDecide: (requestId: string, approve: boolean) => void
}

const ago = (iso: string) => {
  const min = Math.max(1, Math.round((Date.now() - new Date(iso).getTime()) / 60000))
  return min < 60 ? `${min}분 전` : min < 1440 ? `${Math.round(min / 60)}시간 전` : `${Math.round(min / 1440)}일 전`
}

/** 명단에 없는 ID로 들어온 참여 요청. 수락하면 바로 입장, 거절하면 학생에게 안내된다 */
export default function JoinRequestList({ requests, busyId, onDecide }: Props) {
  return (
    <section className="panel stack">
      <div className="spread">
        <h3>참여 요청</h3>
        <span className={`chip ${requests.length ? 'warn' : ''}`}>{requests.length}건</span>
      </div>
      {!requests.length && <p className="note">기다리는 요청이 없어요.</p>}
      {requests.map((r) => (
        <div className="spread" key={r.id}>
          <div className="stack" style={{ gap: 2 }}>
            <b>{r.alias}</b>
            <span className="note">{ago(r.requested_at)} 요청 · 명단에 없는 ID</span>
          </div>
          <div className="row">
            <button className="btn sm primary" disabled={busyId === r.id} onClick={() => onDecide(r.id, true)}>수락</button>
            <button className="btn sm" disabled={busyId === r.id} onClick={() => onDecide(r.id, false)}>거절</button>
          </div>
        </div>
      ))}
    </section>
  )
}
