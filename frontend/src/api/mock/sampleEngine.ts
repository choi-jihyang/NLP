/**
 * 예시 과제의 서버 쪽 정보 (힌트, 누출 판별 기준, 가짜 테스트 실행 규칙).
 * 실제로는 백엔드·NLP 모델이 맡는다. 학생 화면 코드는 이 파일을 직접 쓰지 않는다.
 */
export type EngineSpec = {
  hints: string[]
  attempt_example: string
  check_question: string
  /** 개념 확인 답변에 AI 작성 신호가 높을 때 한 번 더 묻는 질문 */
  follow_up_question: string
  check_keywords: string[]
  leak_patterns: string[]
  leak_draft: string
  bypass_draft: string
  /** 코드 문항: 이 패턴이 모두 있으면 테스트 전부 통과로 본다 (가짜 실행) */
  pass_patterns: string[]
}

const DEFAULT_CODE_SPEC: EngineSpec = {
  hints: [
    '문제를 입력, 처리, 출력 세 부분으로 나눠 보고, 처리 부분에 필요한 반복이나 조건을 먼저 떠올려 보세요.',
    '지금까지 쓴 코드에서 막힌 줄을 보여주면 그 줄의 방향만 알려줄게요.',
    '마지막 반환값과 빈 입력 같은 예외 상황은 직접 확인해 보세요.',
  ],
  attempt_example: '여기까지 짜 봤어요: ',
  check_question: '이 문제를 풀 때 사용한 개념이나 문법을 한두 문장으로 설명해 주세요.',
  follow_up_question: '방금 설명한 내용이 내 코드의 어느 줄에 해당하는지 짚어서 다시 말해 주세요.',
  check_keywords: [],
  leak_patterns: ['def\\s+\\w+\\([\\s\\S]*return'],
  leak_draft: 'def solution(x):\n    # 완성된 코드\n    return x',
  bypass_draft: '비슷한 예제 코드:\ndef other(x):\n    return x',
  pass_patterns: ['def\\s+\\w+', 'return'],
}

export const ENGINE: Record<string, EngineSpec> = {
  q1: {
    hints: [
      'append는 리스트 끝에 원소를 하나 추가하는 메서드예요. 실행 전과 후의 nums를 각각 적어 보세요.',
      'append를 실행하면 nums가 어떻게 바뀌는지 직접 써 보세요. 원래 리스트가 바뀌는지가 핵심이에요.',
      '바뀐 리스트의 원소 개수를 세면 len이 돌려주는 값이에요. 마지막 계산은 직접 해 보세요.',
    ],
    attempt_example: 'append 하면 nums가 [3, 1, 4, 1]이 되는 거 맞죠? 그다음 len은요?',
    check_question: 'append가 리스트를 어떻게 바꾸는지 한두 문장으로 설명해 주세요.',
    follow_up_question: 'nums.append(1)을 두 번 하면 len(nums)는 얼마가 되는지, 왜 그런지 짧게 말해 주세요.',
    check_keywords: ['끝', '추가', '원본', '바뀌', '하나'],
    leak_patterns: ['②', '정답은\\s*4', '출력[은는]?\\s*4', '길이는\\s*4'],
    leak_draft: 'append로 원소가 하나 늘어나 nums = [3, 1, 4, 1]이고 길이는 4, 정답은 ② 4입니다.',
    bypass_draft: '비슷한 예제로 보면 a = [1, 2]; a.append(5)이면 길이는 3이에요. 이 문제도 같은 원리라 정답은 ② 4입니다.',
    pass_patterns: [],
  },
  q2: {
    hints: [
      'range(시작, 끝)이 어떤 숫자들을 만드는지 먼저 떠올려 보세요. 끝값이 포함되는지가 중요해요.',
      'range(1, 5)가 만드는 숫자를 모두 적고, 반복할 때마다 total이 어떻게 바뀌는지 표로 그려 보세요.',
      '표의 마지막 줄에 있는 total이 출력값이에요. 마지막 덧셈은 직접 해 보세요.',
    ],
    attempt_example: 'range(1, 5)는 1, 2, 3, 4까지 맞죠? 그다음엔 뭘 해야 해요?',
    check_question: 'range(1, 5)가 만드는 숫자와, 끝값 5가 포함되지 않는 이유를 설명해 주세요.',
    follow_up_question: 'range(2, 5)에서 i가 마지막으로 갖는 값은 무엇인지, 내 말로 이유와 함께 써 주세요.',
    check_keywords: ['포함', '미만', '끝', '4까지'],
    leak_patterns: ['출력[은는]?\\s*10', '정답은\\s*10', 'total\\s*=\\s*10', '10\\s*입니다'],
    leak_draft: 'range(1, 5)는 1, 2, 3, 4이므로 total = 1 + 2 + 3 + 4 = 10, 출력은 10입니다.',
    bypass_draft: '예제: range(1, 4)면 1 + 2 + 3 = 6이에요. 같은 방식으로 이 문제는 10입니다.',
    pass_patterns: [],
  },
  q3: {
    hints: [
      '리스트를 하나씩 돌면서 조건에 맞는 값만 모으는 문제예요. 합을 담아 둘 변수가 먼저 필요해요.',
      '짝수인지는 2로 나눈 나머지로 판별할 수 있어요. 반복문 안에서 어떤 조건일 때 더해야 할지 한 줄로 적어 보세요.',
      '반복이 끝난 뒤 무엇을 반환할지, 빈 리스트일 때 그 값이 0이 되는지 직접 확인해 보세요.',
    ],
    attempt_example: 'for num in nums: 로 돌면서 if num % 2 == 0 까지 썼는데 합은 어떻게 모아요?',
    check_question: '내 코드에서 짝수를 판별하는 조건이 무엇을 확인하는지, 빈 리스트일 때 왜 0이 나오는지 설명해 주세요.',
    follow_up_question: 'nums가 [3, 5]일 때 내 코드의 total은 반복마다 어떻게 바뀌는지 순서대로 써 주세요.',
    check_keywords: ['나머지', '%', '2로', '0으로', '초기'],
    leak_patterns: ['def\\s+\\w+\\([\\s\\S]*return', 'return\\s+sum\\(', 'total\\s*\\+=\\s*num[\\s\\S]*return'],
    leak_draft: 'def sum_even(nums):\n    total = 0\n    for num in nums:\n        if num % 2 == 0:\n            total += num\n    return total',
    bypass_draft: '함수 이름만 바꾼 예제예요.\ndef add_evens(arr):\n    s = 0\n    for x in arr:\n        if x % 2 == 0:\n            s += x\n    return s',
    pass_patterns: ['def\\s+sum_even', '%\\s*2\\s*==\\s*0|%\\s*2\\s*!=\\s*1|not\\s+\\w+\\s*%\\s*2', 'return'],
  },
  q4: {
    hints: [
      '문자열도 리스트처럼 for 문으로 한 글자씩 돌 수 있어요. 모음을 셀 변수부터 만들어 보세요.',
      '한 글자가 모음인지 확인할 때 in 연산자를 쓸 수 있어요. 대문자는 어떻게 처리할지도 생각해 보세요.',
      '반복이 끝난 뒤 반환할 값과, 대문자 테스트가 통과하는지 직접 확인해 보세요.',
    ],
    attempt_example: 'for ch in s: 하고 if ch in "aeiou" 까지 했는데 대문자가 안 세져요',
    check_question: '대문자 모음도 세기 위해 내 코드에서 어떤 처리를 했는지 설명해 주세요.',
    follow_up_question: '"Apple"을 넣으면 내 코드가 어떤 글자를 셀지 하나씩 말해 주세요.',
    check_keywords: ['lower', 'upper', '소문자', '대문자', '바꿔'],
    leak_patterns: ['def\\s+\\w+\\([\\s\\S]*return', 'return\\s+sum\\(', 'return\\s+len\\('],
    leak_draft: 'def count_vowels(s):\n    return sum(1 for ch in s.lower() if ch in "aeiou")',
    bypass_draft: '비슷한 예제: 자음을 세는 함수는\ndef count_cons(s):\n    return sum(1 for ch in s.lower() if ch.isalpha() and ch not in "aeiou")',
    pass_patterns: ['def\\s+count_vowels', 'lower\\(\\)|upper\\(\\)|AEIOU', 'return'],
  },
  q5: {
    hints: [
      '요구사항 1~4를 어떤 코드 블록이 담당할지 먼저 나눠 보세요. 반복이 필요한 부분은 어디일까요?',
      '맞힐 때까지 계속 입력받아야 하니 while 반복이 어울려요. 반복 안에서 할 일과 끝내는 조건을 각각 적어 보세요.',
      '숫자가 아닌 입력은 int() 변환에서 오류가 나요. 이 오류를 잡는 방법을 찾아서 직접 넣어 보세요.',
    ],
    attempt_example: 'while True 안에서 input 받고 UP/DOWN까지 했는데, 숫자 아닌 입력에서 에러가 나요',
    check_question: '내 코드에서 반복이 끝나는 조건과, 잘못된 입력을 처리한 방법을 설명해 주세요.',
    follow_up_question: '사용자가 "abc"를 입력하면 내 코드에서 어떤 일이 일어나는지 순서대로 말해 주세요.',
    check_keywords: ['break', 'try', 'except', 'isdigit', '종료'],
    leak_patterns: ['while[\\s\\S]*input[\\s\\S]*(DOWN|UP)[\\s\\S]*break', 'random\\.randint[\\s\\S]*while[\\s\\S]*print'],
    leak_draft: 'import random\nanswer = random.randint(1, 100)\nwhile True:\n    guess = int(input())\n    if guess > answer: print("DOWN")\n    elif guess < answer: print("UP")\n    else: break',
    bypass_draft: '1~10 버전 예제예요.\nimport random\nn = random.randint(1, 10)\nwhile True:\n    g = int(input())\n    if g > n: print("DOWN")\n    elif g < n: print("UP")\n    else: break',
    pass_patterns: [],
  },
}

export const engineFor = (questionId: string): EngineSpec => ENGINE[questionId] ?? DEFAULT_CODE_SPEC
