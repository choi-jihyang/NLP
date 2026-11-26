# 과제: 2진수 변환기 · 덧셈기 · 뺄셈기

> ThinkGuard 과제 파일 양식 예시 (초안). 이 파일을 PDF로 저장해 "과제 파일에서 가져오기"에 올린다.
> `[교수자 전용]` 표시가 붙은 항목(정답·숨김 테스트·채점 기준·모범 답안·확인 문제)은 학생에게 보이지 않는다.

## 과제 정보
- 제목: 2진수 변환기 · 덧셈기 · 뺄셈기
- 과목: 프로그래밍 기초
- 대상: 컴퓨터공학과 1학년
- 언어: C
- 마감: 2026-12-05 23:59
- 설명: 10진수와 2진수를 오가는 원리를 이해하고, 자리올림(carry)과 빌림(borrow)을 직접 구현한다. 2진수는 정수형으로 바꾸지 않고 문자열로 다룬다(3·4·5번).

---

## 문항 1
- 유형: 객관식
- 배점: 10

### 문제
2진수 `1011`을 10진수로 바꾸면 얼마인가?

### 선택지
1. 11
2. 13
3. 1011
4. 3

### 정답 [교수자 전용]
1

### 오개념 [교수자 전용]
- 2: 자리값을 왼쪽부터 1, 2, 4, 8로 읽음
- 3: 2진수를 10진수처럼 그대로 읽음
- 4: 자리값을 곱하지 않고 숫자만 더함

### 확인 문제 [교수자 전용]
- 유형: 객관식
- 문제: 2진수 `1101`을 10진수로 바꾸면 얼마인가?
- 선택지: 1. 13 / 2. 11 / 3. 1101 / 4. 3
- 정답: 1

---

## 문항 2
- 유형: 출력 예측
- 배점: 10

### 문제
다음 프로그램의 출력을 쓰시오.

### 코드
```c
#include <stdio.h>

int main(void) {
    int n = 13;
    for (int i = 3; i >= 0; i--) {
        printf("%d", (n >> i) & 1);
    }
    printf("\n");
    return 0;
}
```

### 정답 [교수자 전용]
1101

### 인정 답안 [교수자 전용]
- 1101
- 1 1 0 1

### 확인 문제 [교수자 전용]
- 유형: 출력 예측
- 문제: 위 코드에서 `int n = 13;`을 `int n = 6;`으로 바꾸면 출력은?
- 정답: 0110

---

## 문항 3
- 유형: 코드 작성
- 배점: 20

### 문제
10진수 정수 `n`을 입력받아 2진수로 출력하는 `print_binary` 함수를 완성하시오.
- 입력: 0 이상 1,000,000 이하의 정수 `n` 한 줄
- 출력: `n`을 2진수로 쓴 것. 앞에 0을 붙이지 않는다. `n`이 0이면 `0`
- `printf("%b")`처럼 2진수를 바로 출력하는 기능은 쓰지 않는다.

### 시작 코드
```c
#include <stdio.h>

void print_binary(unsigned int n) {
    // 여기에 작성
}

int main(void) {
    unsigned int n;
    scanf("%u", &n);
    print_binary(n);
    printf("\n");
    return 0;
}
```

### 공개 테스트
```text
입력: 5
출력: 101
---
입력: 0
출력: 0
---
입력: 8
출력: 1000
```

### 숨김 테스트 [교수자 전용]
```text
입력: 1
출력: 1
---
입력: 255
출력: 11111111
---
입력: 1000000
출력: 11110100001001000000
```

### 모범 답안 [교수자 전용]
```c
#include <stdio.h>

void print_binary(unsigned int n) {
    char bits[33];
    int len = 0;

    if (n == 0) {
        printf("0");
        return;
    }
    while (n > 0) {
        bits[len++] = (char)('0' + (n % 2));
        n /= 2;
    }
    for (int i = len - 1; i >= 0; i--) {
        printf("%c", bits[i]);
    }
}

int main(void) {
    unsigned int n;
    scanf("%u", &n);
    print_binary(n);
    printf("\n");
    return 0;
}
```

---

## 문항 4
- 유형: 코드 작성
- 배점: 25

### 문제
두 2진수 `a`, `b`를 입력받아 합을 2진수로 출력하는 `add_binary` 함수를 완성하시오.
- 입력: 공백으로 구분된 2진수 두 개. 각각 1자리 이상 100자리 이하, `0`과 `1`만 있고 앞에 0이 없다(0 자체는 `0`).
- 출력: `a + b`를 2진수로 쓴 것. 앞에 0을 붙이지 않는다.
- 100자리는 정수형(`long long`)에 담을 수 없으므로 **문자열 그대로** 오른쪽 자리부터 더한다.

### 시작 코드
```c
#include <stdio.h>
#include <string.h>

#define MAX_LEN 100

void add_binary(const char *a, const char *b, char *result) {
    // 여기에 작성
}

int main(void) {
    char a[MAX_LEN + 1], b[MAX_LEN + 1];
    char result[MAX_LEN + 2];
    scanf("%100s %100s", a, b);
    add_binary(a, b, result);
    printf("%s\n", result);
    return 0;
}
```

### 공개 테스트
```text
입력: 1011 110
출력: 10001
---
입력: 0 0
출력: 0
---
입력: 1 1
출력: 10
```

### 숨김 테스트 [교수자 전용]
```text
입력: 1111 1
출력: 10000
---
입력: 101 0
출력: 101
---
입력: 1111111111111111111111111111111111111111111111111111111111111111111111 1
출력: 10000000000000000000000000000000000000000000000000000000000000000000000
```

### 모범 답안 [교수자 전용]
```c
#include <stdio.h>
#include <string.h>

#define MAX_LEN 100

void add_binary(const char *a, const char *b, char *result) {
    int i = (int)strlen(a) - 1;
    int j = (int)strlen(b) - 1;
    int carry = 0;
    char reversed[MAX_LEN + 2];
    int len = 0;

    while (i >= 0 || j >= 0 || carry) {
        int sum = carry;
        if (i >= 0) sum += a[i--] - '0';
        if (j >= 0) sum += b[j--] - '0';
        reversed[len++] = (char)('0' + sum % 2);
        carry = sum / 2;
    }
    for (int k = 0; k < len; k++) {
        result[k] = reversed[len - 1 - k];
    }
    result[len] = '\0';
}

int main(void) {
    char a[MAX_LEN + 1], b[MAX_LEN + 1];
    char result[MAX_LEN + 2];
    scanf("%100s %100s", a, b);
    add_binary(a, b, result);
    printf("%s\n", result);
    return 0;
}
```

---

## 문항 5
- 유형: 간단 제작
- 배점: 35
- AI 도움: 사용

### 문제
두 2진수 `a`, `b`를 입력받아 `a - b`를 2진수로 출력하는 뺄셈기를 만드시오.
- 입력: 문항 4와 같은 형식(각 100자리 이하, 앞에 0 없음)
- 출력: `a - b`를 2진수로 쓴 것. 결과가 음수면 앞에 `-`를 붙인다. 결과가 0이면 `0`
- 빌림(borrow) 방식이나 2의 보수 방식 중 하나로 구현하고, **어떤 방식을 썼는지 주석으로 설명**한다.
- 정수형으로 바꿔 계산하지 않는다.

### 채점 기준 [교수자 전용]
- a ≥ b일 때 빌림을 처리해 결과가 맞다 (10점)
- a < b일 때 `-`를 붙여 결과가 맞다 (10점)
- 결과의 앞자리 0을 지우고, 결과가 0이면 `0`을 출력한다 (5점)
- 100자리 입력을 정수형 변환 없이 처리한다 (5점)
- 사용한 방식(빌림 또는 2의 보수)을 주석으로 설명했다 (5점)

### 모범 답안 [교수자 전용]
```c
#include <stdio.h>
#include <string.h>

#define MAX_LEN 100

/* 크기 비교: a > b면 1, 같으면 0, a < b면 -1 (둘 다 앞자리 0 없음) */
int compare_binary(const char *a, const char *b) {
    int la = (int)strlen(a), lb = (int)strlen(b);
    if (la != lb) return la > lb ? 1 : -1;
    int c = strcmp(a, b);
    return (c > 0) - (c < 0);
}

/* 빌림(borrow) 방식: 큰 수 - 작은 수, 오른쪽 자리부터 뺀다 */
void sub_binary(const char *big, const char *small, char *result) {
    int i = (int)strlen(big) - 1;
    int j = (int)strlen(small) - 1;
    int borrow = 0;
    char reversed[MAX_LEN + 1];
    int len = 0;

    while (i >= 0) {
        int d = (big[i--] - '0') - borrow;
        if (j >= 0) d -= small[j--] - '0';
        if (d < 0) {
            d += 2;
            borrow = 1;
        } else {
            borrow = 0;
        }
        reversed[len++] = (char)('0' + d);
    }
    while (len > 1 && reversed[len - 1] == '0') {
        len--; /* 앞자리 0 지우기 */
    }
    for (int k = 0; k < len; k++) {
        result[k] = reversed[len - 1 - k];
    }
    result[len] = '\0';
}

int main(void) {
    char a[MAX_LEN + 1], b[MAX_LEN + 1];
    char result[MAX_LEN + 1];
    scanf("%100s %100s", a, b);

    int cmp = compare_binary(a, b);
    if (cmp >= 0) {
        sub_binary(a, b, result);
        printf("%s\n", result);
    } else {
        sub_binary(b, a, result);
        printf("-%s\n", result);
    }
    return 0;
}
```

### 참고 입출력 [교수자 전용]
```text
입력: 1011 110
출력: 101
---
입력: 110 1011
출력: -101
---
입력: 1010 1010
출력: 0
---
입력: 1000000000000000000000000000000000000000000000000000000000000000000000 1
출력: 111111111111111111111111111111111111111111111111111111111111111111111
```
