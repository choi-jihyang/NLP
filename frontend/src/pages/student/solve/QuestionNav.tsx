import type { AnswerState, StudentQuestion } from '../../../api/submissions'

type Props = {
  questions: StudentQuestion[]
  answers: Record<string, AnswerState>
  current: number
  onSelect: (index: number) => void
}

const DOT = { DRAFT: '', AWAITING_CHECK: 'wait', SUBMITTED: 'done' } as const
const LABEL = { DRAFT: '아직 안 냄', AWAITING_CHECK: '개념 확인 중', SUBMITTED: '제출함' } as const

/** 문항 번호 이동. 점은 제출 여부만 보여준다 (정오는 결과 공개 전까지 숨김) */
export default function QuestionNav({ questions, answers, current, onSelect }: Props) {
  return (
    <nav className="qnav" aria-label="문항 이동">
      {questions.map((q, i) => {
        const status = answers[q.id]?.status ?? 'DRAFT'
        return (
          <button key={q.id} className="qn" aria-current={i === current} aria-label={`문항 ${i + 1} · ${LABEL[status]}`} onClick={() => onSelect(i)}>
            {i + 1}
            <span className={`dot ${DOT[status]}`} />
          </button>
        )
      })}
    </nav>
  )
}
