import { useState } from 'react'
import { useParams } from 'react-router-dom'

import { PageHead } from '../../../components/PageHead'
import { QueryState } from '../../../components/QueryState'
import { useAssignmentDraft } from '../../../hooks/useAssignmentDraft'
import StepPolicy from './policy/StepPolicy'
import StepLoad from './StepLoad'
import Stepper from './Stepper'
import StepQuestions from './StepQuestions'
import StepReview from './StepReview'

/** 교수자: 과제 만들기 · 고치기 (불러오기 → 문항 · 채점 → AI 도움 정책 → 확인 · 배포) */
export default function AssignmentEditorPage() {
  const { classId: classParam, assignmentId: assignmentParam } = useParams()
  const classId = Number(classParam)
  const assignmentId = assignmentParam ? Number(assignmentParam) : undefined
  const { draft, query, loaded, load, update, updatePolicy, updateQuestion, setQuestions } = useAssignmentDraft(classId, assignmentId)
  const [step, setStep] = useState(1)
  const [fileName, setFileName] = useState<string | null>(null)

  if (!draft) return <main className="wrap page"><QueryState isPending={query.isPending} error={query.error} /></main>
  const go = (n: number) => {
    setStep(n)
    window.scrollTo({ top: 0 })
  }

  return (
    <>
    <PageHead
      back={{ to: `/teacher/classes/${classId}`, label: '클래스' }}
      eyebrow={assignmentId ? 'Edit assignment' : 'New assignment'}
      title={assignmentId ? draft.title || '과제 설정' : '새 과제'}
    >
      <div style={{ marginTop: 22 }}><Stepper step={step} enabled={loaded} onSelect={go} /></div>
    </PageHead>
    <main className="wrap page">
      {step === 1 && (
        <StepLoad
          draft={draft}
          loaded={loaded}
          loading={load.isPending}
          fileName={fileName}
          error={load.error}
          onChange={update}
          onFile={(file) => {
            setFileName(file.name)
            load.mutate({ kind: 'FILE', file })
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
      {step === 4 && <StepReview draft={draft} onSaved={(saved) => update({ seq: saved.seq, questions: saved.questions })} onPrev={() => go(3)} />}
    </main>
    </>
  )
}
