import type { AnswerState } from '../../../api/submissions'

type Props = { answer: AnswerState; changed: boolean; finalized: boolean }

const time = (iso: string) => new Date(iso).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Seoul' })

/** 제출한 문항 안내. 정오와 점수는 교수자가 결과를 공개할 때까지 보여주지 않는다 */
export default function SubmittedNote({ answer, changed, finalized }: Props) {
  if (answer.status !== 'SUBMITTED' || !answer.submitted_at) return null
  return (
    <div className="status wait">
      <div>✓</div>
      <div className="stack" style={{ gap: 2 }}>
        <b>{time(answer.submitted_at)}에 제출했어요</b>
        <span className="note">
          {finalized
            ? '최종 제출한 과제예요. 결과와 정답은 교수자가 공개하면 볼 수 있어요.'
            : changed
              ? '제출한 답과 지금 답이 달라요. 다시 제출해야 바뀐 답이 채점돼요.'
              : '최종 제출 전까지 고쳐서 다시 낼 수 있어요. 결과와 정답은 교수자가 공개하면 볼 수 있어요.'}
        </span>
      </div>
    </div>
  )
}
