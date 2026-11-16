import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'

import { getStudentAssignment } from '../../../api/submissions'
import { formatDue } from '../../../components/format'
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
  const { assignmentId = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [debug, setDebug] = useState(false)

  const assignment = useQuery({ queryKey: ['student-assignment', assignmentId], queryFn: () => getStudentAssignment(assignmentId) })
  const { submission, query, submit, conceptCheck, cancelCheck, finalize, run } = useSubmission(assignmentId)

  const questions = assignment.data?.questions ?? []
  const index = Math.min(Number(params.get('q') ?? 0) || 0, Math.max(questions.length - 1, 0))
  const q = questions[index]
  const qid = q?.id ?? ''
  const { chat, send } = useChat(assignmentId, qid)
  const paste = usePasteLog(qid, assignment.data?.external_signal_enabled ?? false)

  if (!assignment.data || !submission || !q) {
    return <QueryState isPending={assignment.isPending || query.isPending} error={assignment.error ?? query.error} />
  }
  const a = assignment.data
  const answer = submission.answers[qid]
  const draft = drafts[qid] ?? (answer.content || q.starter_code)
  const busy = submit.isPending || conceptCheck.isPending || cancelCheck.isPending || finalize.isPending || run.isPending
  const submittedCount = questions.filter((x) => submission.answers[x.id]?.status === 'SUBMITTED').length
  const finalized = submission.finalized

  return (
    <div>
      <div className="sbar">
        <h2>{a.title}</h2>
        <span className="note">
          {a.course} · {a.language} · 마감 {formatDue(a.due_at)}
        </span>
        <label className="check">
          <input type="checkbox" checked={debug} onChange={(e) => setDebug(e.target.checked)} />
          판별 과정 표시 (시연용)
        </label>
      </div>
      {a.external_signal_enabled && (
        <p className="flow">이 과제는 붙여넣기 길이와 시점을 기록해요. 붙여 넣은 내용은 저장하지 않아요.</p>
      )}
      <QuestionNav
        questions={questions}
        answers={submission.answers}
        current={index}
        onSelect={(i) => setParams({ q: String(i) }, { replace: true })}
      />
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
    </div>
  )
}
