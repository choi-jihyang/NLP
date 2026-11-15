# 커밋 메시지 컨벤션

```
[이름] 작업내용 타이틀

* 세부내용1
* 세부내용2
```

- `[이름]` = **브랜치 이름에서 `/` 뒤 부분**. `feature`/`fix` 같은 종류는 적지 않는다.
  - `feature/login-api` → `[login-api]`
  - `feature/solve-screen` → `[solve-screen]`
  - `fix/hint-leak` → `[hint-leak]`
  - `develop`·`main`에 바로 하는 커밋(문서·설정 정리 등) → `[develop]` / `[main]`
- 제목은 한국어로, "무엇을 했는지"를 쓴다. 마침표 없이.
- 제목 다음 **빈 줄 1개**, 본문은 `*` 불릿.
- 본문이 필요 없는 한 줄짜리 변경은 제목만 써도 된다.
- 한 커밋 = 한 가지 의미 있는 변경. 기능과 포맷 정리를 섞지 않는다.
- Claude가 만든 커밋은 마지막 줄에 `Co-Authored-By:` 줄을 남겨도 된다.

### 예시
```
[policy-branch] 분류 결과에 따른 응답 정책 분기 추가

* 완성 답안 요청 + 시도 근거 없음 → 힌트만
* 모호하면 LLM 호출 없이 시도 여부 되묻기
* test_policy.py 6개 케이스
```
