/** 선택지 번호 기호와 "② 4" 같은 표시 문자열 */
export const CIRCLED = ['①', '②', '③', '④', '⑤', '⑥']

export const choiceLabel = (choices: string[], index: string) =>
  `${CIRCLED[Number(index)] ?? ''} ${choices[Number(index)] ?? ''}`.trim()
