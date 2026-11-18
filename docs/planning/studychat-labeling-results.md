# StudyChat 라벨링 통합 결과

통합일: 2026-11-18. 상태: **AI 라벨 초안 통합 완료, 사람 검토 전**.

## 범위와 결과

StudyChat 16,851건을 원본 순서의 앞 15,764건과 팀원 담당 1,087건으로 나눠 처리했다.
초기 팀원 패키지의 나머지 RECIPE4U 1,913건은 이번 통합에서 제외했다.

| 상태 | 건수 |
|---|---:|
| 형식·근거 검증 통과 (`ok`) | 15,092 |
| 입력 길이 초과 (`context_overflow`) | 781 |
| 출력 검증 실패 (`invalid_output`) | 978 |
| 전체 고유 ID | 16,851 |

- 원본 ID 기준 누락·중복·예상 외 ID: 각각 0건.
- 기존 성공 7,430건은 그대로 보존했다.
- 팀원 검증 통과 977건을 포함했다. 팀원 실패 110건은 성공 학습 라벨에서 제외했다.
- 중단된 이전 실행의 체크포인트에서 내보내기 파일에 빠졌던 추가 성공 24건을 복구했다.
- 성공 중 세 라벨 모두 결정된 행은 14,991건, 하나 이상 `null`인 행은 101건이다.
- 성공 시도 사이 판단 불일치 1개 ID는 비공개 검토 목록에 따로 기록했다.

`ok`는 원문 인용·학생 역할·스키마·필드 일관성 검증 통과를 뜻한다.
의미 정확도나 사람 정답을 보증하지 않으며 `human_reviewed=false`, `gold_eligible=false`를 유지한다.

## 실행 방식

- 초기: Qwen3.5-9B FP8, vLLM, 입력 6,000토큰.
- 재처리: A100 80GB, 공식 Qwen3.5-9B BF16, 기존 성공 제외.
- 최종 재처리: 입력 32,000토큰 이하만 대상, 원문 무절단, 출력 2,048토큰, 최대 2회 시도.
- 길이 캐시·대화/길이 정렬·배치 2/4/8 비교를 적용하고 배치 8을 선택했다.
- 배치 비교에서 성공한 행도 본 실행에서 재사용했다.
- 32K 초과 입력과 반복 검증 실패는 성공으로 바꾸지 않고 보존했다.

## 재현 및 검사

현재 권장 실행 노트북은 `notebooks/thinkguard_studychat_a100_32k_optimized.ipynb`이다.
팀원 실행본은 `notebooks/thinkguard_team_last3000.ipynb`에 보존한다.
Git에는 코드와 출력 없는 노트북만 보관한다. 원문·식별자·파생 주석은 Git 제외 `data/raw/` 아래에 둔다.

```powershell
python -m unittest discover -s nlp/colab -p 'test_*.py'
python -m unittest discover -s nlp -p test_annotation_safety.py
```

실제 비공개 원본과 결과 스냅샷이 로컬에 있을 때:

```powershell
python nlp/integrate_studychat_final.py --team-annotations '<팀원 annotations.jsonl 경로>'
python nlp/verify_final_studychat.py
```

원본 입력은 `data/raw/colab_bundle/inputs.jsonl.gz`, 수집한 결과는
`data/raw/colab_merge_20261118/`, 통합 산출물은 `data/raw/studychat_final_20261118/`에 둔다.
다운로드 출처 목록은 인증된 Drive에서 수집한 비공개 메타데이터다. 일회성 인증 링크는 Git에 올리지 않는다.

## 선택·통합 불변식

원본 ID·입력/원본 SHA·학생/대화 ID·담당 범위를 대조한다.
모든 성공 후보의 `raw_response`를 원본 입력에 대해 다시 검증한다(I4).
원래 성공을 우선 보존하고, 실패 ID는 이전 재처리·배치 비교·본 실행 순서의 첫 검증 통과 결과로 복구한다.
여러 시도는 출처별로 기록하되 최종 출력은 원본 ID마다 한 건이다.
일부 원본/팀원 실행의 전체 설정 파일은 확보되지 않아 모든 실행 환경의 완전 재현을 주장하지 않는다.

비공개 결과 파일:

- `studychat_ok.jsonl`: 검증 통과 행만 포함한다. `null`을 `false`로 바꾸지 않는다.
- `studychat_all_16851.jsonl`: 실패까지 포함한 전체 상태.
- `studychat_failures.jsonl`: 학습 라벨에서 제외할 실패 목록.
- `lineage.jsonl`, `sources_and_configs.json`, `SHA256.json`: 선택 출처와 산출물 무결성.
- `label_conflicts.json`: 성공 시도 사이 불일치 검토 대상.

다음 단계는 사람 독립 검토와 학생·대화 그룹 단위 학습/검증/평가 분리다.
라벨링 산출물을 서비스 분류기의 검증된 성능이나 독립 평가 정답으로 취급하지 않는다.
