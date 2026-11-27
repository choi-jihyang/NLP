import type { AnswerState, StudentQuestion } from '../../../api/submissions'
import { TYPE_LABEL } from '../../../components/questionType'

type Props = {
  questions: StudentQuestion[]
  answers: Record<string, AnswerState>
  current: number
  onSelect: (index: number) => void
}

const CLASS = { DRAFT: '', AWAITING_CHECK: ' wait', SUBMITTED: ' done' } as const
const MARK = { DRAFT: '', AWAITING_CHECK: ' · 확인 중', SUBMITTED: ' ✓' } as const
const LABEL = { DRAFT: '아직 안 냄', AWAITING_CHECK: '개념 확인 중', SUBMITTED: '제출함' } as const

/** 문항 바로가기 알약. 표시는 제출 여부만 (정오는 결과 공개 전까지 숨김) */
export default function QuestionNav({ questions, answers, current, onSelect }: Props) {
  return (
    <nav className="qbar" aria-label="문항 이동">
      {questions.map((q, i) => {
        const status = answers[q.seq]?.status ?? 'DRAFT'
        return (
          <button
            key={q.seq}
            type="button"
            className={`${i === current ? 'on' : ''}${CLASS[status]}`}
            aria-current={i === current}
            aria-label={`문항 ${i + 1} · ${LABEL[status]}`}
            onClick={() => onSelect(i)}
          >
            <b>{i + 1}</b>
            {TYPE_LABEL[q.type]}
            {MARK[status]}
          </button>
        )
      })}
    </nav>
  )
}
