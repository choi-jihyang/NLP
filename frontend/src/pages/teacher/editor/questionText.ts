import type { Question, QuestionType } from '../../../api/assignments'
import { TYPE_LABEL } from '../../../components/questionType'

export { TYPE_LABEL }

export const totalPoints = (qs: Question[]) => qs.reduce((sum, q) => sum + q.points, 0)

export const typeSummary = (qs: Question[]) =>
  (Object.keys(TYPE_LABEL) as QuestionType[]).map((t) => `${TYPE_LABEL[t]} ${qs.filter((q) => q.type === t).length}개`).join(', ')

let seq = 0

/** 직접 추가하는 빈 문항 */
export function newQuestion(type: QuestionType): Question {
  seq += 1
  return {
    id: `new-${Date.now()}-${seq}`,
    type,
    points: type === 'PROJECT' ? 20 : type === 'CODE' ? 10 : 5,
    prompt: '',
    code: '',
    choices: type === 'MULTIPLE_CHOICE' ? ['', '', '', ''] : [],
    answer: type === 'MULTIPLE_CHOICE' ? '0' : '',
    accepted_answers: [],
    misconceptions: {},
    starter_code: '',
    tests: type === 'CODE' ? [{ call: '', expected: '', hidden: false }] : [],
    rubric: type === 'PROJECT' ? [''] : [],
    model_answer: '',
    ai_help: true,
    variant: null,
  }
}
