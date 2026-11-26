import { useState } from 'react'

import type { AnswerState, ConceptReply, RunResult, StudentQuestion } from '../../../api/submissions'
import type { PasteField } from '../../../api/pasteEvents'
import { AnswerInput } from '../../../components/AnswerInput'
import { CodeBlock } from '../../../components/CodeBlock'
import { TYPE_LABEL } from '../../../components/questionType'
import { TestResults } from '../../../components/TestResults'
import ConceptCheckBox from './ConceptCheckBox'
import SubmittedNote from './SubmittedNote'

type Props = {
  index: number
  question: StudentQuestion
  answer: AnswerState
  draft: string
  finalized: boolean
  busy: boolean
  onDraftChange: (value: string) => void
  onRun: (code: string) => Promise<RunResult>
  onSubmit: (value: string) => void
  onConceptAnswer: (body: ConceptReply) => void
  onConceptCancel: () => void
  onPaste: (field: PasteField) => (length: number) => void
}

/** 왼쪽 문항 카드: 문제, 답 입력, 공개 테스트 실행, 제출, 제출 전 개념 확인 */
export default function QuestionCard(props: Props) {
  const { index, question: q, answer, draft, finalized, busy, onDraftChange, onRun, onSubmit, onPaste } = props
  const [runResults, setRunResults] = useState<RunResult | null>(null)
  const [runError, setRunError] = useState<string | null>(null)
  const checking = answer.status === 'AWAITING_CHECK'
  const editable = !finalized && !checking
  const submitted = answer.status === 'SUBMITTED'
  const changed = submitted && draft !== answer.content
  const hasAnswer = draft.trim().length > 0 && draft !== q.starter_code

  return (
    <section className="panel stack">
      <div className="row">
        <b>문항 {index + 1}</b>
        <span className="chip">{TYPE_LABEL[q.type]}</span>
        <span className="chip">{q.points}점</span>
      </div>
      <p className="qtext">{q.prompt}</p>
      <CodeBlock code={q.code} />
      {q.type === 'CODE' && (
        <span className="note">
          공개 테스트 {q.public_tests.length}개는 제출 전에 실행해 볼 수 있어요. 숨김 테스트 {q.hidden_test_count}개는 채점할 때만 실행돼요.
        </span>
      )}
      <AnswerInput
        id={`answer-${q.seq}`}
        type={q.type}
        choices={q.choices}
        value={finalized ? answer.content : draft}
        onChange={onDraftChange}
        disabled={!editable}
        onPaste={onPaste('ANSWER')}
      />
      {editable && runError && <p className="error-text">{runError}</p>}
      {editable && runResults && (
        <div className="stack" style={{ gap: 6 }}>
          <span className="label">실행 결과 · 공개 테스트</span>
          <TestResults run={runResults} />
        </div>
      )}
      {checking && answer.concept_check && (
        <ConceptCheckBox
          key={answer.concept_check.answered}
          check={answer.concept_check}
          busy={busy}
          onAnswer={props.onConceptAnswer}
          onCancel={props.onConceptCancel}
          onPaste={onPaste('CONCEPT_CHECK')}
        />
      )}
      {editable && (
        <div className="row">
          {q.type === 'CODE' && (
            <button className="btn" disabled={busy || !hasAnswer} onClick={async () => {
                setRunError(null)
                try {
                  setRunResults(await onRun(draft))
                } catch (e) {
                  // 실행기(Docker)가 꺼져 있으면 503 RUNNER_UNAVAILABLE — 학생에게 안내만 하고 화면은 그대로
                  setRunResults(null)
                  setRunError(e instanceof Error ? e.message : '코드를 실행하지 못했어요.')
                }
              }}>
              공개 테스트 실행
            </button>
          )}
          <button className="btn primary" disabled={busy || !hasAnswer || (submitted && !changed)} onClick={() => onSubmit(draft)}>
            {submitted ? '다시 제출' : '제출'}
          </button>
        </div>
      )}
      <SubmittedNote answer={answer} changed={changed} finalized={finalized} />
    </section>
  )
}
