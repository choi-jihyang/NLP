import type { QuestionType } from '../api/assignments'

/** 문항 유형 표시 이름 */
export const TYPE_LABEL: Record<QuestionType, string> = {
  MULTIPLE_CHOICE: '객관식 퀴즈',
  SHORT_ANSWER: '출력 예측',
  CODE: '코드 작성',
  PROJECT: '간단 제작',
}
