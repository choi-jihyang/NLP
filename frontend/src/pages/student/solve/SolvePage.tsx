import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'

import { LANGUAGE_LABEL } from '../../../api/client'
import { getStudentAssignment, type AnswerState } from '../../../api/submissions'
import { formatDue } from '../../../components/format'
import { PageHead } from '../../../components/PageHead'
import { QueryState } from '../../../components/QueryState'
import { useChat } from '../../../hooks/useChat'
import { usePasteLog } from '../../../hooks/usePasteLog'
import { useSubmission } from '../../../hooks/useSubmission'
import ChatPanel from './ChatPanel'
import { chatLock } from './chatLock'
import FinalizeBar from './FinalizeBar'
import QuestionCard from './QuestionCard'
import QuestionNav from './QuestionNav'

/** 학생: 과제 풀이 (왼쪽 문항 · 오른쪽 학습 AI) */
export default function SolvePage() {
  const assignmentId = Number(useParams().assignmentId)
  const [params, setParams] = useSearchParams()
  const [drafts, setDrafts] = useState<Record<number, string>>({})
  const [debug, setDebug] = useState(false)

  const assignment = useQuery({ queryKey: ['student-assignment', assignmentId], queryFn: () => getStudentAssignment(assignmentId) })
  const { submission, query, submit, conceptCheck, cancelCheck, finalize, run } = useSubmission(assignmentId)

  const questions = assignment.data?.questions ?? []
  const index = Math.min(Number(params.get('q') ?? 0) || 0, Math.max(questions.length - 1, 0))
  const q = questions[index]
  const qid = q?.seq ?? null
  const { chat, send } = useChat(assignmentId, qid)
  const paste = usePasteLog(qid, assignment.data?.external_signal_enabled ?? false)

  if (!assignment.data || !submission || !q || qid == null) {
    return (
      <main className="wrap page">
        <QueryState isPending={assignment.isPending || query.isPending} error={assignment.error ?? query.error} />
      </main>
    )
  }
  const a = assignment.data
  // 아직 손대지 않은 문항은 서버에 답이 없다 → 시작 코드로 시작하는 빈 답
  const answer: AnswerState = submission.answers[qid] ?? {
    question_id: qid, content: '', status: 'DRAFT', submitted_at: null, submit_count: 0, hint_step: 0, concept_check: null,
  }
  const draft = drafts[qid] ?? (answer.content || q.starter_code)
  const busy = submit.isPending || conceptCheck.isPending || cancelCheck.isPending || finalize.isPending || run.isPending
  const submittedCount = questions.filter((x) => submission.answers[x.seq]?.status === 'SUBMITTED').length
  const finalized = submission.finalized

  return (
    <>
      <PageHead
        back={{ to: '/student/classes', label: '내 과제' }}
        title={a.title}
        sub={`${a.course} · ${LANGUAGE_LABEL[a.language]} · 마감 ${formatDue(a.due_at)}`}
        actions={
          <>
            {a.external_signal_enabled && (
              <span className="notice">붙여넣기는 길이와 시점만 기록해요. 내용은 저장하지 않아요.</span>
            )}
            <label className="check note">
              <input type="checkbox" checked={debug} onChange={(e) => setDebug(e.target.checked)} />
              판별 과정 표시 (시연용)
            </label>
          </>
        }
      >
        <QuestionNav
          questions={questions}
          answers={submission.answers}
          current={index}
          onSelect={(i) => setParams({ q: String(i) }, { replace: true })}
        />
      </PageHead>
      <main className="wrap page">
      <div className="split">
        <QuestionCard
          key={qid}
          index={index}
          question={q}
          answer={answer}
          draft={draft}
          finalized={finalized}
          busy={busy}
          onDraftChange={(value) => setDrafts((d) => ({ ...d, [qid]: value }))}
          onRun={(code) => run.mutateAsync({ questionId: qid, value: code })}
          onSubmit={(value) => submit.mutate({ questionId: qid, value })}
          onConceptAnswer={(body) => conceptCheck.mutate({ questionId: qid, body })}
          onConceptCancel={() => cancelCheck.mutate(qid)}
          onPaste={paste}
        />
        <ChatPanel
          index={index}
          chat={chat}
          modeLabel={a.hint_mode_label}
          earned={a.hint_mode === 'EARNED'}
          lock={chatLock(q, answer, finalized)}
          sending={send.isPending}
          debug={debug}
          onSend={(body) => send.mutate(body)}
          onPaste={paste('CHAT')}
        />
      </div>
      <FinalizeBar
        assignmentId={assignmentId}
        submitted={submittedCount}
        total={questions.length}
        finalized={finalized}
        busy={busy}
        onFinalize={() => finalize.mutate()}
      />
      {(submit.error || conceptCheck.error || finalize.error || send.error) && (
        <p className="error-text">{(submit.error ?? conceptCheck.error ?? finalize.error ?? send.error)?.message}</p>
      )}
      </main>
    </>
  )
}
