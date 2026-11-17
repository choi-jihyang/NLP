import type { AiPolicy, Question } from '../assignments'

/** 예시 과제: 3주차 과제 · 반복문과 리스트 (Python). 백엔드가 생기면 지운다 */
export const SAMPLE_TITLE = '3주차 과제 · 반복문과 리스트'

export const DEFAULT_POLICY: AiPolicy = {
  hint_mode: 'EARNED',
  code_line_limit: 3,
  hint_penalty: 'NONE',
  variant_enabled: true,
  variant_graded: false,
  concept_check_enabled: true,
  external_signal_enabled: true,
  report_misconceptions: true,
  report_dependency: true,
  prompt_mode: 'FORM',
  custom_prompt: null,
}

const BASE = {
  code: '',
  choices: [],
  answer: '',
  accepted_answers: [],
  misconceptions: {},
  starter_code: '',
  tests: [],
  rubric: [],
  model_answer: '',
  ai_help: true,
  variant: null,
}

export const SAMPLE_QUESTIONS: Question[] = [
  {
    ...BASE,
    id: 'q1',
    type: 'MULTIPLE_CHOICE',
    points: 10,
    prompt: '다음 코드를 실행했을 때 출력되는 값은?',
    code: 'nums = [3, 1, 4]\nnums.append(1)\nprint(len(nums))',
    choices: ['3', '4', '5', '오류 발생'],
    answer: '1',
    misconceptions: {
      '0': 'append가 원본 리스트를 바꾸지 않는다고 착각',
      '2': 'append(1)이 1을 두 번 넣는다고 착각',
      '3': 'append의 반환값(None)을 다시 넣는 코드와 혼동',
    },
    variant: {
      type: 'MULTIPLE_CHOICE',
      prompt: '다음 코드의 출력은?',
      code: 'a = [1, 2]\na.extend([3, 4])\nprint(len(a))',
      choices: ['2', '3', '4', '5'],
      answer: '2',
      accepted_answers: [],
    },
  },
  {
    ...BASE,
    id: 'q2',
    type: 'SHORT_ANSWER',
    points: 10,
    prompt: '다음 코드의 출력값을 쓰시오.',
    code: 'total = 0\nfor i in range(1, 5):\n    total += i\nprint(total)',
    answer: '10',
    accepted_answers: ['10'],
    variant: {
      type: 'SHORT_ANSWER',
      prompt: '다음 코드의 출력값을 쓰시오.',
      code: 'total = 0\nfor i in range(2, 6):\n    total += i\nprint(total)',
      choices: [],
      answer: '14',
      accepted_answers: ['14'],
    },
  },
  {
    ...BASE,
    id: 'q3',
    type: 'CODE',
    points: 20,
    prompt: '정수 리스트 nums를 받아 짝수만 더한 값을 반환하는 함수 sum_even(nums)를 작성하시오. 빈 리스트면 0을 반환합니다.',
    starter_code: 'def sum_even(nums):\n    # 여기에 코드를 작성하세요\n    pass\n',
    tests: [
      { call: 'sum_even([1, 2, 3, 4])', expected: '6', hidden: false },
      { call: 'sum_even([])', expected: '0', hidden: false },
      { call: 'sum_even([-2, 3, 8])', expected: '6', hidden: true },
      { call: 'sum_even([1, 3, 5])', expected: '0', hidden: true },
    ],
    variant: {
      type: 'SHORT_ANSWER',
      prompt: 'sum_even이 올바르게 작성됐을 때, 다음 코드의 출력값을 쓰시오.',
      code: 'print(sum_even([5, 6, 7, 8]))',
      choices: [],
      answer: '14',
      accepted_answers: ['14'],
    },
  },
  {
    ...BASE,
    id: 'q4',
    type: 'CODE',
    points: 20,
    prompt: '문자열 s를 받아 모음(a, e, i, o, u)의 개수를 반환하는 함수 count_vowels(s)를 작성하시오. 대문자도 모음으로 셉니다.',
    starter_code: 'def count_vowels(s):\n    # 여기에 코드를 작성하세요\n    pass\n',
    tests: [
      { call: 'count_vowels("hello")', expected: '2', hidden: false },
      { call: 'count_vowels("")', expected: '0', hidden: false },
      { call: 'count_vowels("AEIOU")', expected: '5', hidden: true },
      { call: 'count_vowels("rhythm")', expected: '0', hidden: true },
    ],
    variant: {
      type: 'SHORT_ANSWER',
      prompt: 'count_vowels가 올바르게 작성됐을 때, 다음 코드의 출력값을 쓰시오.',
      code: 'print(count_vowels("Banana"))',
      choices: [],
      answer: '3',
      accepted_answers: ['3'],
    },
  },
  {
    ...BASE,
    id: 'q5',
    type: 'PROJECT',
    points: 20,
    prompt: '숫자 맞히기 게임을 만드시오. 아래 요구사항을 모두 만족해야 합니다.',
    code: '요구사항\n1. 1~100 사이의 정답을 무작위로 정한다\n2. 입력이 정답보다 크면 "DOWN", 작으면 "UP"을 출력한다\n3. 맞히면 시도 횟수와 함께 종료한다\n4. 숫자가 아닌 입력에는 다시 입력하라고 안내한다',
    starter_code: 'import random\n\n# 여기에 코드를 작성하세요\n',
    rubric: [
      '정답을 무작위로 정함 · 4점',
      'UP/DOWN 비교가 정확함 · 6점',
      '시도 횟수를 세고 맞히면 종료함 · 5점',
      '잘못된 입력을 처리함 · 5점',
    ],
    model_answer:
      'import random\nanswer = random.randint(1, 100)\ncount = 0\nwhile True:\n    try:\n        guess = int(input("숫자: "))\n    except ValueError:\n        print("숫자만 입력해 주세요")\n        continue\n    count += 1\n    if guess > answer:\n        print("DOWN")\n    elif guess < answer:\n        print("UP")\n    else:\n        print(f"정답! {count}번 만에 맞혔어요")\n        break',
  },
]
