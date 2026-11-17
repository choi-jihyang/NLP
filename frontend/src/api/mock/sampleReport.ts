/** 반 리포트 예시 데이터 (가상 학급 32명 중 28명 제출) */
import type { AssignmentReport } from '../reports'

export const SAMPLE_REPORT: AssignmentReport = {
  assignment_id: 'a1',
  title: '3주차 과제 · 반복문과 리스트',
  submitted_count: 28,
  student_count: 32,
  assisted_correct_rate: 73,
  alone_variant_rate: 57,
  concept_check_ok_rate: 72,
  question_stats: [
    { question_index: 0, type_label: '객관식 퀴즈', correct_rate: 82, variant_rate: 68, avg_hint_steps: 1.1 },
    { question_index: 1, type_label: '출력 예측', correct_rate: 71, variant_rate: 55, avg_hint_steps: 1.7 },
    { question_index: 2, type_label: '코드 작성', correct_rate: 76, variant_rate: 58, avg_hint_steps: 2.2 },
    { question_index: 3, type_label: '코드 작성', correct_rate: 64, variant_rate: 47, avg_hint_steps: 2.5 },
  ],
  mistakes: [
    {
      question_index: 0,
      kind: 'CHOICE',
      rows: [
        { label: '① 3', rate: 14, note: 'append가 원본 리스트를 바꾸지 않는다고 착각', correct: false },
        { label: '② 4', rate: 71, note: null, correct: true },
        { label: '③ 5', rate: 9, note: null, correct: false },
        { label: '④ 오류 발생', rate: 6, note: null, correct: false },
      ],
    },
    {
      question_index: 1,
      kind: 'ANSWER',
      rows: [
        { label: '15', rate: 22, note: 'range의 끝값 5까지 포함된다고 생각', correct: false },
        { label: '4', rate: 8, note: '합 대신 마지막 i 값을 출력한다고 생각', correct: false },
      ],
    },
    {
      question_index: 2,
      kind: 'TEST',
      rows: [
        { label: 'sum_even([])', rate: 21, note: '빈 리스트에서 0 대신 None 반환 (return 위치 오류)', correct: false },
        { label: 'sum_even([-2, 3, 8])', rate: 12, note: '음수 짝수를 빼고 계산', correct: false },
      ],
    },
    {
      question_index: 3,
      kind: 'TEST',
      rows: [
        { label: 'count_vowels("AEIOU")', rate: 34, note: '대문자를 모음으로 세지 않음', correct: false },
        { label: 'count_vowels("")', rate: 6, note: '빈 문자열 처리 누락', correct: false },
      ],
    },
  ],
  supplement: {
    question_index: 1,
    rate: 22,
    summary:
      'range(1, 5)에 끝값 5가 포함된다고 생각한 학생이 많아요. 문항 3의 빈 리스트 테스트 실패(21%)도 반복 범위를 놓친 경우가 많아요.',
    items: [
      'list(range(3, 7)) 의 출력은?',
      'for i in range(5): 가 반복하는 횟수와 i의 마지막 값은?',
      'range를 써서 1부터 10까지(10 포함) 출력하는 코드를 한 줄로 쓰시오.',
    ],
  },
  dependency: [
    { student_id: 's03', student_name: '학생 03', question_index: 2, hint_steps: 3, variant_answer: '12', cause: '짝수 판별 조건을 % 2 == 1로 씀' },
    { student_id: 's07', student_name: '학생 07', question_index: 1, hint_steps: 2, variant_answer: '20', cause: 'range 끝값 포함으로 계산' },
    { student_id: 's11', student_name: '학생 11', question_index: 3, hint_steps: 3, variant_answer: '2', cause: '대문자 처리 누락' },
    { student_id: 's15', student_name: '학생 15', question_index: 2, hint_steps: 3, variant_answer: '26', cause: '짝수 대신 전체 합을 계산' },
    { student_id: 's22', student_name: '학생 22', question_index: 0, hint_steps: 2, variant_answer: '④ 5', cause: 'extend와 append 혼동' },
  ],
  signals: [
    { student_id: 's09', student_name: '학생 09', question_index: 2, signals: ['답 칸에 붙여넣기 (214자)', '풀이 시간 40초', '개념 확인 답변에 AI 작성 신호 → 추가 질문'] },
    { student_id: 's13', student_name: '학생 13', question_index: 4, signals: ['답 칸에 붙여넣기 (612자)', '코드 블록 서식(```)', 'AI 답변 특유 표현'] },
    { student_id: 's20', student_name: '학생 20', question_index: 3, signals: ['채팅에 코드 블록 붙여넣기', 'AI 답변 특유 표현'] },
    { student_id: 's27', student_name: '학생 27', question_index: 0, signals: ['풀이 시간 6초'] },
  ],
}
