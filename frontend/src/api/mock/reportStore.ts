/** 리포트·채점·이해 확인 예시 저장소. 백엔드 API가 생기면 지운다 */
import type { MyReportResponse } from '../reports'
import type { CheckReceipt, CheckSubmission, UnderstandingCheck } from '../understanding'
import { respondWith } from './delay'
import { isAnswerCorrect } from './grading'
import { progress } from './progress'
import { SAMPLE_GRADING, SAMPLE_MY_REPORT, SAMPLE_RECORD } from './sampleRecords'
import { SAMPLE_QUESTIONS } from './sampleQuestions'
import { SAMPLE_REPORT } from './sampleReport'

const grading = SAMPLE_GRADING.map((g) => ({ ...g }))
const checkQuestions = SAMPLE_QUESTIONS.filter((q) => q.variant).slice(0, 2)
const checkLog: { question_id: string; correct: boolean; overconfident: boolean }[] = []

export const mockReports = {
  report: (_assignmentId: string) => respondWith(SAMPLE_REPORT),
  grading: (_assignmentId: string) => respondWith(grading),
  grade: (answerId: string, body: { score: number; feedback: string }) => {
    const item = grading.find((g) => g.answer_id === answerId)
    if (!item) return Promise.reject(new Error('답안을 찾을 수 없어요'))
    if (body.score < 0 || body.score > item.points) return Promise.reject(new Error(`0~${item.points}점 사이로 입력해 주세요`))
    Object.assign(item, body)
    return respondWith(item)
  },
  record: (_assignmentId: string, studentId: string) => respondWith({ ...SAMPLE_RECORD, student_id: studentId }),
  myReport: (assignmentId: string) =>
    respondWith<MyReportResponse>(
      progress.released.has(assignmentId)
        ? { released: true, ...SAMPLE_MY_REPORT }
        : { released: false, assignment_title: SAMPLE_MY_REPORT.assignment_title },
    ),
  check: (_assignmentId: string) =>
    respondWith<UnderstandingCheck>({
      explain_prompt:
        '문항 3에서 내가 쓴 짝수 판별 조건이 무엇을 확인하는지, 그리고 "홀수만 더하라"로 요구사항이 바뀌면 내 코드에서 어디를 고쳐야 하는지 설명해 주세요.',
      explain_code: 'def sum_even(nums):\n    total = 0\n    for num in nums:\n        if num % 2 == 0:\n            total += num\n    return total',
      items: checkQuestions.map((q) => ({
        question_id: q.id,
        type: q.variant!.type,
        prompt: q.variant!.prompt,
        code: q.variant!.code,
        choices: q.variant!.choices,
      })),
    }),
  submitCheck: (_assignmentId: string, body: CheckSubmission) => {
    // 정오와 "확실한데 틀림"은 교수자 리포트·결과 공개 뒤 내 리포트에 쓴다. 학생에게 바로 돌려주지 않는다
    checkLog.push(
      ...body.answers.map((a) => {
        const variant = checkQuestions.find((q) => q.id === a.question_id)?.variant
        const correct = variant ? isAnswerCorrect(variant, a.value) : false
        return { question_id: a.question_id, correct, overconfident: !correct && a.confidence === 'SURE' }
      }),
    )
    return respondWith<CheckReceipt>({ submitted_at: new Date().toISOString() }, 300)
  },
}
