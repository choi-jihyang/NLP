import { useState } from 'react'
import { useParams } from 'react-router-dom'

import { QueryState } from '../../../components/QueryState'
import { useAssignmentDraft } from '../../../hooks/useAssignmentDraft'
import StepPolicy from './policy/StepPolicy'
import StepLoad from './StepLoad'
import Stepper from './Stepper'
import StepQuestions from './StepQuestions'
import StepReview from './StepReview'

/** 교수자: 과제 만들기 · 고치기 (불러오기 → 문항 · 채점 → AI 도움 정책 → 확인 · 배포) */
export default function AssignmentEditorPage() {
  const { classId = '', assignmentId } = useParams()
  const { draft, query, loaded, load, update, updatePolicy, updateQuestion, setQuestions } = useAssignmentDraft(classId, assignmentId)
  const [step, setStep] = useState(1)
  const [fileName, setFileName] = useState<string | null>(null)

  if (!draft) return <QueryState isPending={query.isPending} error={query.error} />
  const go = (n: number) => {
    setStep(n)
    window.scrollTo({ top: 0 })
  }

  return (
    <div>
      <Stepper step={step} enabled={loaded} onSelect={go} />
      {step === 1 && (
        <StepLoad
          draft={draft}
          loaded={loaded}
          loading={load.isPending}
          fileName={fileName}
          error={load.error}
          onChange={update}
          onFile={(name) => {
            setFileName(name)
            load.mutate({ kind: 'FILE', fileName: name })
          }}
          onSample={() => {
            setFileName(null)
            load.mutate({ kind: 'SAMPLE' })
          }}
          onBlank={() => {
            setFileName(null)
            load.mutate({ kind: 'BLANK' })
          }}
          onNext={() => go(2)}
        />
      )}
      {step === 2 && (
        <StepQuestions questions={draft.questions} onChange={updateQuestion} onReplace={setQuestions} onPrev={() => go(1)} onNext={() => go(3)} />
      )}
      {step === 3 && <StepPolicy draft={draft} onChange={updatePolicy} onPrev={() => go(2)} onNext={() => go(4)} />}
      {step === 4 && <StepReview draft={draft} onSaved={(saved) => update({ id: saved.id })} onPrev={() => go(3)} />}
    </div>
  )
}
