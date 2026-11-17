/** 학생 쪽 예시 저장소 (내 제출, 문항별 대화, 붙여넣기 기록). 백엔드 API가 생기면 지운다 */
import type { Assignment, Question } from '../assignments'
import type { ChatRequest, ChatState, ChatTurn } from '../chat'
import type { PasteEvent } from '../pasteEvents'
import type { AnswerState, ConceptReply, StudentAssignment, Submission } from '../submissions'
import { MAX_STEPS, respond, shouldOfferChoices } from './chatEngine'
import { aiWritingSignals, isHighSignal, mentionsConcept } from './conceptCheck'
import { respondWith } from './delay'
import { runTests } from './grading'
import { HINT_MODE_LABEL } from './policyText'
import { progress } from './progress'
import { engineFor } from './sampleEngine'
import { DEFAULT_POLICY, SAMPLE_QUESTIONS, SAMPLE_TITLE } from './sampleQuestions'

/** 학생이 보는 과제. 지금은 배포된 예시 과제(a1) 하나 */
const assignment: Assignment = {
  id: 'a1', class_id: 'c1', title: SAMPLE_TITLE, course: '프로그래밍 기초', audience: '대학 1학년',
  language: 'Python', description: '', due_at: '2026-11-20T23:59:00+09:00', published: true,
  policy: DEFAULT_POLICY, questions: SAMPLE_QUESTIONS,
}
const answers: Record<string, AnswerState> = {}
const chats: Record<string, ChatTurn[]> = {}
/** 붙여넣기는 길이와 시점만 남긴다 (불변식 I5) */
export const pasteLog: PasteEvent[] = []

const question = (id: string): Question => {
  const q = assignment.questions.find((x) => x.id === id)
  if (!q) throw new Error('문항을 찾을 수 없어요')
  return q
}
const answerOf = (id: string): AnswerState =>
  (answers[id] ??= { question_id: id, content: question(id).starter_code, status: 'DRAFT', submitted_at: null, hint_step: 0, concept_check: null })

/** 교수자만 보는 개념 확인 기록 (답변 · AI 작성 신호). 학생 응답에는 넣지 않는다 */
export const conceptLog: { question_id: string; question: string; reply: string; mentions_concept: boolean; signals: string[] }[] = []

function markSubmitted(qid: string) {
  Object.assign(answerOf(qid), { status: 'SUBMITTED', submitted_at: new Date().toISOString() })
  progress.submitted[assignment.id] = assignment.questions.filter((q) => answerOf(q.id).status === 'SUBMITTED').length
}

/** 힌트 없이 처음 내는 문항이면 개념 확인부터 */
const needsCheck = (q: Question, a: AnswerState) =>
  assignment.policy.concept_check_enabled && q.type !== 'PROJECT' && a.hint_step === 0 && a.submitted_at === null

/** 채점은 백엔드가 마감·결과 공개 때 한다. 학생 응답에는 정오·점수를 넣지 않는다 */
function submission(): Submission {
  return {
    assignment_id: assignment.id,
    answers: Object.fromEntries(assignment.questions.map((q) => [q.id, answerOf(q.id)])),
    finalized: progress.finalized.has(assignment.id),
    results_released: progress.released.has(assignment.id),
  }
}

const locked = () => progress.finalized.has(assignment.id)

function chatState(id: string): ChatState {
  return {
    question_id: id,
    turns: chats[id] ?? [],
    hint_step: answerOf(id).hint_step,
    max_hint_steps: MAX_STEPS[assignment.policy.hint_mode],
    usage_remaining: 30 - Object.values(chats).flat().filter((t) => t.role === 'STUDENT').length,
  }
}

export const mockStudent = {
  assignment: (_id: string) =>
    respondWith<StudentAssignment>({
      id: assignment.id, title: assignment.title, course: assignment.course, language: assignment.language,
      due_at: assignment.due_at, hint_mode: assignment.policy.hint_mode,
      hint_mode_label: HINT_MODE_LABEL[assignment.policy.hint_mode],
      max_hint_steps: MAX_STEPS[assignment.policy.hint_mode],
      external_signal_enabled: assignment.policy.external_signal_enabled,
      questions: assignment.questions.map((q) => ({
        id: q.id, type: q.type, points: q.points, prompt: q.prompt, code: q.code, choices: q.choices,
        starter_code: q.starter_code, ai_help: q.ai_help, ai_enabled: q.type !== 'PROJECT' || q.ai_help,
        public_tests: q.tests.filter((t) => !t.hidden), hidden_test_count: q.tests.filter((t) => t.hidden).length,
      })),
    }),
  submission: (_id: string) => respondWith(submission()),
  runPublicTests: (_id: string, qid: string, code: string) => respondWith(runTests(question(qid), code, false), 300),
  submitAnswer: (_id: string, qid: string, content: string) => {
    if (locked()) return Promise.reject(new Error('최종 제출한 과제는 답을 고칠 수 없어요.'))
    const q = question(qid), a = answerOf(qid)
    a.content = content
    if (needsCheck(q, a)) {
      a.status = 'AWAITING_CHECK'
      a.concept_check ??= { questions: [engineFor(qid).check_question], answered: 0 }
    } else markSubmitted(qid)
    return respondWith(submission(), 300)
  },
  answerConceptCheck: (_id: string, qid: string, body: ConceptReply) => {
    const a = answerOf(qid), check = a.concept_check
    if (a.status !== 'AWAITING_CHECK' || !check) return Promise.reject(new Error('답할 개념 확인 질문이 없어요.'))
    const signals = aiWritingSignals(body)
    conceptLog.push({
      question_id: qid, question: check.questions[check.answered], reply: body.reply,
      mentions_concept: mentionsConcept(engineFor(qid).check_keywords, body.reply), signals,
    })
    check.answered += 1
    // 첫 답변에 AI 작성 신호가 높으면 한 번만 더 묻는다. 점수에는 반영하지 않는다
    if (check.answered === 1 && isHighSignal(signals)) check.questions.push(engineFor(qid).follow_up_question)
    if (check.answered >= check.questions.length) markSubmitted(qid)
    return respondWith(submission(), 300)
  },
  cancelConceptCheck: (_id: string, qid: string) => {
    answerOf(qid).status = 'DRAFT'
    return respondWith(submission())
  },
  finalize: (_id: string) => {
    if (assignment.questions.some((q) => answerOf(q.id).status !== 'SUBMITTED')) {
      return Promise.reject(new Error('아직 내지 않은 문항이 있어요.'))
    }
    progress.finalized.add(assignment.id)
    return respondWith(submission(), 300)
  },
  chat: (_id: string, qid: string) => respondWith(chatState(qid)),
  sendChat: (req: ChatRequest) => {
    if (locked()) return Promise.reject(new Error('최종 제출한 뒤에는 AI 도움을 쓸 수 없어요.'))
    if (answerOf(req.question_id).status === 'AWAITING_CHECK') return Promise.reject(new Error('개념 확인 질문에 먼저 답해 주세요.'))
    const turns = (chats[req.question_id] ??= [])
    const a = answerOf(req.question_id)
    const student = (text: string): ChatTurn => ({ role: 'STUDENT', text, response_mode: null, trace: null })
    const bot = (text: string, mode: ChatTurn['response_mode'], trace: ChatTurn['trace'] = null): ChatTurn => ({ role: 'ASSISTANT', text, response_mode: mode, trace })
    if (req.choice === 'FEEDBACK') turns.push(bot('좋아요. 지금까지 짠 코드나 막힌 줄을 보내 주세요. 한 줄이어도 괜찮아요.', 'ASK_ATTEMPT'))
    else if (!req.choice && shouldOfferChoices(req.message, assignment.policy)) {
      turns.push(student(req.message), bot('완성된 답을 바로 받기보다, 아래에서 골라 볼래요?', 'OFFER_CHOICES'))
    } else {
      const message = req.choice === 'FIRST_HINT' ? '첫 힌트 주세요' : req.message
      if (req.choice !== 'ORIGINAL') turns.push(student(message))
      const r = respond(req.question_id, message, a.hint_step, assignment.policy)
      a.hint_step = r.next_step
      turns.push(bot(r.reply, r.mode, r.trace))
    }
    return respondWith(chatState(req.question_id), 350)
  },
  logPaste: (event: PasteEvent) => {
    pasteLog.push({ question_id: event.question_id, field: event.field, length: event.length, pasted_at: event.pasted_at })
    return respondWith({ ok: true }, 0)
  },
}
