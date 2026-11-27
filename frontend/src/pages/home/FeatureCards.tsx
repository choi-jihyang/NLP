import { ChatDemo } from './ChatDemo'
import { useSeen } from './useReveal'

const TRACE: [string, string, string][] = [
  ['k', '▸ 요청 분류', '완성 답안 요청'],
  ['k', '▸ 시도 근거', '학생 메시지 0건'],
  ['k', '▸ 응답 정책', '도움 방식 고르기'],
  ['k', '▸ 누출 검사', '완성 코드 없음 ✓'],
]
const BARS: [string, number, boolean][] = [['반복문', 86, false], ['나머지 연산', 72, false], ['배열 역순', 41, true], ['자리 올림', 33, true]]

/** 메인 ②: 정답 대신 다음 한 단계 — 살아 있는 미니 화면 카드 4개 (예시) */
export function FeatureCards() {
  const [termRef, termSeen] = useSeen<HTMLDivElement>()
  const [barRef, barSeen] = useSeen<HTMLDivElement>()
  return (
    <section className="block" id="features">
      <div className="wrap">
        <div className="sec-head reveal">
          <div>
            <p className="eyebrow">How it helps</p>
            <h2 style={{ marginTop: 10 }}>정답 대신,<br />다음 한 단계</h2>
          </div>
          <p className="muted">학생이 무엇을 시도했는지 보고 도움의 크기를 정해요. 과제가 끝나면 정말 이해했는지 AI 없이 확인해요.</p>
        </div>
        <div className="cards">
          <div className="card c7 reveal">
            <div className="stage"><ChatDemo /></div>
            <div className="foot"><b>AI 튜터</b><span>시도한 만큼 열리는 힌트</span></div>
          </div>
          <div className="card c5 reveal d1">
            <div className="stage dark term" ref={termRef}>
              <div className="bar"><span>판별 과정</span><span>·</span><span>문항 3 · 코드 작성</span></div>
              <div className={`ln${termSeen ? ' on' : ''}`}><span className="prompt">❯</span> "코드 전체 짜주세요"</div>
              {TRACE.map(([, k, v], i) => (
                <div key={k} className={`ln${termSeen ? ' on' : ''}`} style={{ transitionDelay: `${(i + 1) * 0.4}s` }}>
                  <span className="k">{k}</span> <span className={i === 3 ? 'g' : i === 1 ? 'd' : 'w'}>{v}</span>
                </div>
              ))}
              <div className={`ln d${termSeen ? ' on' : ''}`} style={{ transitionDelay: '2s' }}>◆ 힌트 1단계로 답변</div>
            </div>
            <div className="foot"><b>판별 과정</b><span>요청 → 근거 → 정책</span></div>
          </div>
          <div className="card c4 reveal">
            <div className="stage">
              <div className="qcard">
                <p className="q">내 함수 <span className="mono">to_bin(6)</span>의 출력은?</p>
                <div className="qopt"><i />011</div>
                <div className="qopt sel"><i />110</div>
                <div className="hconf">확신 <b className="on" /><b className="on" /><b className="on" /><b /></div>
              </div>
              <p className="muted" style={{ fontSize: '.84rem' }}>AI 도움 없이 · 숫자만 바꾼 확인 문제</p>
            </div>
            <div className="foot"><b>이해 확인</b><span>AI 없음</span></div>
          </div>
          <div className="card c8 reveal d1">
            <div className="stage" ref={barRef}>
              <div className="spread" style={{ marginBottom: 16 }}>
                <b style={{ fontFamily: 'var(--f-display)' }}>반 리포트 · 2진수 변환기</b>
                <span className="mono muted" style={{ fontSize: '.78rem' }}>예시</span>
              </div>
              <div className="bars">
                {BARS.map(([name, w, warn]) => (
                  <div key={name} className="bar-row">
                    <span>{name}</span>
                    <span className="tr"><i className={warn ? 'warn' : undefined} style={{ width: barSeen ? `${w}%` : 0 }} /></span>
                    <span className="v">{w}%</span>
                  </div>
                ))}
              </div>
              <p className="mis">자주 나온 오개념 · 나머지를 거꾸로 읽지 않고 순서대로 출력했어요</p>
            </div>
            <div className="foot"><b>반 리포트</b><span>개념별 이해 · 오개념 · 참고 신호</span></div>
          </div>
        </div>
      </div>
    </section>
  )
}
