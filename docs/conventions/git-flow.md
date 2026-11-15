# git-flow (간소)

| 브랜치 | 분기 출처 | 머지 대상 | 네이밍 |
|---|---|---|---|
| `main` | — | — | 시연 가능한 안정 버전 (마일스톤마다 머지) |
| `develop` | `main` | `main` | 통합 |
| 기능 | `develop` | `develop` (PR) | `feature/<짧은이름>` |
| 버그 수정 | `develop` | `develop` (PR) | `fix/<짧은이름>` |
| 문서 | `develop` | `develop` (PR) | `docs/<짧은이름>` |

- 기능 브랜치 → PR → `develop` 머지(`--no-ff`).
- 중간 점검일(11/17 · 11/24 · 12/1) 전에 `develop` → `main` 머지 후 태그를 단다: `m1-1117`, `m2-1124`, `m3-1201`.
- 브랜치 이름은 영어 소문자 kebab-case. 예: `feature/class-invite-code`, `fix/paste-log-length`.
- 머지된 기능 브랜치는 삭제한다.
- 커밋 메시지: [commit-convention.md](commit-convention.md) · PR 크기: [pr-convention.md](pr-convention.md)
