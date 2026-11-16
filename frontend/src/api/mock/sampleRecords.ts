/** 간단 제작 답안, 학생별 기록, 내 리포트 예시 데이터 */
import type { GradingItem, MyReport, StudentRecord } from '../reports'
import { SAMPLE_QUESTIONS } from './sampleQuestions'

const project = SAMPLE_QUESTIONS[4]

export const SAMPLE_GRADING: GradingItem[] = [
  {
    answer_id: 'ans-05', student_name: '학생 05', question_index: 4, points: project.points, rubric: project.rubric,
    signals: [], score: null, feedback: '',
    content: 'import random\nans = random.randint(1, 100)\ntries = 0\nwhile True:\n    s = input("> ")\n    if not s.isdigit():\n        print("숫자를 입력하세요")\n        continue\n    tries += 1\n    g = int(s)\n    if g > ans: print("DOWN")\n    elif g < ans: print("UP")\n    else:\n        print(tries, "번 만에 정답")\n        break',
  },
  {
    answer_id: 'ans-13', student_name: '학생 13', question_index: 4, points: project.points, rubric: project.rubric,
    signals: ['답 칸에 붙여넣기 (612자)', '코드 블록 서식(```)', 'AI 답변 특유 표현'], score: null, feedback: '',
    content: '다음과 같이 숫자 맞히기 게임을 구현할 수 있습니다.\n\n```python\nimport random\n\ndef play_game():\n    """1~100 숫자 맞히기 게임"""\n    answer = random.randint(1, 100)\n    attempts = 0\n    while True:\n        try:\n            guess = int(input("숫자를 입력하세요: "))\n        except ValueError:\n            print("올바른 숫자를 입력해 주세요.")\n            continue\n        attempts += 1\n        ...\n```',
  },
  {
    answer_id: 'ans-24', student_name: '학생 24', question_index: 4, points: project.points, rubric: project.rubric,
    signals: [], score: null, feedback: '',
    content: 'import random\na = random.randint(1,100)\nwhile True:\n    g = int(input())\n    if g > a:\n        print("DOWN")\n    elif g < a:\n        print("UP")\n    else:\n        print("정답")\n        break',
  },
]

export const SAMPLE_RECORD: StudentRecord = {
  student_id: 's03',
  student_name: '학생 03',
  assignment_title: '3주차 과제 · 반복문과 리스트',
  score: 50,
  max_score: 80,
  pending_points: 20,
  variant_passed: 2,
  variant_total: 4,
  variant_note: '문항 2·3은 힌트로만 맞힘',
  hint_steps: 7,
  class_avg_hint_steps: 4.1,
  rows: [
    { question_index: 0, hint_steps: 0, result: '정답', variant: '정답', concept_check: '설명 확인', signal: null },
    { question_index: 1, hint_steps: 1, result: '정답', variant: '오답 (20)', concept_check: '—', signal: null },
    { question_index: 2, hint_steps: 3, result: '테스트 4/4 통과', variant: '오답 (12)', concept_check: '—', signal: null },
    { question_index: 3, hint_steps: 1, result: '테스트 2/4 통과', variant: '정답', concept_check: '—', signal: '답 칸에 붙여넣기 (214자)' },
    { question_index: 4, hint_steps: 2, result: '채점 대기', variant: '—', concept_check: '—', signal: null },
  ],
  conversation: {
    question_index: 2,
    turns: [
      { message: 'sum_even 코드 전체 짜주세요', classification: '완성 답안 요청', attempt: false, leak_blocked: true },
      { message: 'for num in nums 하고 if num % 2 == 1 까지 썼는데 테스트가 틀려요', classification: '풀이 공유', attempt: true, leak_blocked: false },
    ],
    note: '추정 오개념: 짝수 판별 조건을 % 2 == 1로 씀. 힌트 3단계 뒤 테스트는 통과했지만 확인 문제에서 같은 실수가 다시 나왔어요. 확정 판정이 아니라 교수자가 확인할 근거예요.',
  },
}

export const SAMPLE_MY_REPORT: MyReport = {
  assignment_title: '3주차 과제 · 반복문과 리스트',
  score: 50,
  max_score: 80,
  pending_points: 20,
  hint_steps: 7,
  concepts: [
    { name: '리스트 메서드 (append)', status: 'CONFIRMED', reason: '퀴즈와 확인 문제를 힌트 없이 맞혔고, 설명에 "원본 리스트 끝에 추가된다"는 원리가 들어 있어요.' },
    { name: '문자열 순회와 in 연산자', status: 'CONFIRMED', reason: 'count_vowels를 힌트 1단계로 작성했고, 출력 예측 문제도 맞혔어요.' },
    { name: 'range의 범위', status: 'NEEDS_WORK', reason: '원문제는 힌트 1단계로 맞혔지만, AI 없는 확인 문제에서 끝값까지 포함해 20으로 답했어요.' },
    { name: '조건문과 나머지 연산', status: 'UNCLEAR', reason: '테스트는 통과했지만 힌트 3단계를 받았고, 내 함수의 출력 예측 문제를 틀려서 판단 근거가 엇갈려요.' },
  ],
  misconceptions: ['range(a, b)에 끝값 b가 포함된다고 생각했어요.', '짝수 판별을 num % 2 == 1로 썼다가 힌트를 받고 고쳤어요.'],
  overconfident: ['range 출력 예측 문제'],
  next_steps: ['강의자료 3주차: range와 반복 범위', '추천 유사 문제: list(range(2, 8, 2))의 출력은?'],
  questions: [
    { question_index: 0, type_label: '객관식 퀴즈', result: '정답', correct_answer: '② 4 — append는 원본 리스트 끝에 하나를 더해요.' },
    { question_index: 1, type_label: '출력 예측', result: '정답 (힌트 1단계)', correct_answer: '10 — range(1, 5)는 1, 2, 3, 4예요.' },
    { question_index: 2, type_label: '코드 작성', result: '테스트 4/4 통과 (힌트 3단계)', correct_answer: 'num % 2 == 0인 값만 total에 더하고, 반복이 끝난 뒤 return' },
    { question_index: 3, type_label: '코드 작성', result: '테스트 2/4 통과', correct_answer: 's.lower()로 바꾼 뒤 각 글자가 "aeiou"에 있는지 세기 (실패: 대문자, 빈 문자열)' },
    { question_index: 4, type_label: '간단 제작', result: '채점 대기', correct_answer: '교수자 채점 후 피드백이 표시돼요' },
  ],
}
