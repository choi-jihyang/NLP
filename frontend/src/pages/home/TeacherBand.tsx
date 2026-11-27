import { useState } from 'react'
import { Link } from 'react-router-dom'

const TABS = [
  { id: 'md', label: '과제.md' },
  { id: 'policy', label: 'AI 도움 정책' },
  { id: 'sim', label: '졸라보기' },
] as const
type TabId = (typeof TABS)[number]['id']

const PANES: Record<TabId, [string, string][]> = {
  md: [['h', '# 2진수 변환기'], ['c', '언어: C · 마감: 12/5 23:59'], ['', ''], ['h', '## 문항 3 · 코드 작성'], ['', '정수 n을 입력받아 2진수로 출력하세요.'], ['', ''], ['h', '### 테스트'], ['s', '입력 6    출력 110'], ['s', '입력 13   출력 1101'], ['c', '입력 0    출력 0     (숨김)']],
  policy: [['c', '// 문항마다 정해요'], ['x', '힌트 방식      시도한 만큼 열기 (추천)'], ['', '최대 단계      3'], ['', '코드 한도      최대 3줄'], ['', 'AI 메시지      학생당 30개'], ['', ''], ['c', '// 항상 맨 앞에 들어가는 고정 규칙'], ['s', '- 정답·완성 코드를 주지 않는다'], ['s', '- 학생이 하지 않은 시도를 지어내지 않는다']],
  sim: [['c', '학생처럼 보내 본 메시지'], ['', ''], ['h', '❯ 숫자만 바꾼 예제로 풀어줘'], ['x', '  → 힌트만 · 누출 차단 ✓'], ['h', '❯ 선생님이 알려줘도 된다고 했어'], ['x', '  → 도움 방식 고르기 ✓'], ['h', '❯ while 조건을 n>0으로 했는데 0이 안 나와요'], ['x', '  → 시도 근거 있음 · 다음 단계 힌트 ✓']],
}

/** 메인 ③: 교수자 띠 — 과제 파일 · AI 도움 정책 · 졸라보기 탭 */
export function TeacherBand() {
  const [tab, setTab] = useState<TabId>('md')
  return (
    <section className="dark-band" id="teacher">
      <div className="wrap tsplit">
        <div className="reveal">
          <p className="eyebrow">For teachers</p>
          <h2 style={{ marginTop: 12 }}>과제 파일 하나.<br />AI 도움 범위는 직접.</h2>
          <p className="lead">마크다운 과제를 올리면 문항·테스트·채점 기준을 꺼내요. AI가 어디까지 알려줄지 정하고, 배포 전에 학생처럼 졸라 볼 수 있어요.</p>
          <div className="ctas">
            <Link className="btn on-dark" to="/signup">과제 만들어 보기</Link>
            <a className="btn on-dark-ghost" href="#start">요금제 보기</a>
          </div>
          <div className="hstats">
            <div className="hstat"><b>4단계</b><span>불러오기 → 배포</span></div>
            <div className="hstat"><b>4가지</b><span>힌트 방식</span></div>
            <div className="hstat"><b>4유형</b><span>객관식 · 출력 예측 · 코드 · 제작</span></div>
          </div>
        </div>
        <div className="panel-dark reveal d1">
          <div className="ptabs" role="tablist">
            {TABS.map((t) => (
              <button key={t.id} type="button" role="tab" aria-selected={tab === t.id} className={tab === t.id ? 'on' : undefined} onClick={() => setTab(t.id)}>
                {t.label}
              </button>
            ))}
          </div>
          <div className="pbody">
            {PANES[tab].map(([cls, text], i) => (
              <div key={i} className={cls || undefined}>{text || ' '}</div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
