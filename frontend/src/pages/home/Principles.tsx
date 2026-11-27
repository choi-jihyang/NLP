const ITEMS = [
  { title: '정답을 주지 않아요', text: '완성 풀이·완성 코드는 응답 전에 한 번 더 걸러요.', label: 'LEAK CHECK', icon: 'M12 3 4 6v6c0 4.5 3.4 8.3 8 9 4.6-.7 8-4.5 8-9V6l-8-3Z M9 12l2 2 4-4' },
  { title: '시도를 지어내지 않아요', text: '근거는 학생이 보낸 메시지에서만 찾아요.', label: 'STUDENT ONLY', icon: 'M4 5h16v11H8l-4 4V5Z M9 10h6' },
  { title: '붙여넣기는 길이·시점만', text: '붙여넣은 내용은 저장하지 않아요.', label: 'NO CONTENT', icon: 'M7 4h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z M10 8h4M10 12h4' },
  { title: '의심 신호는 참고용', text: '외부 AI 신호로 점수를 바꾸거나 재풀이를 요구하지 않아요.', label: 'SIGNAL ONLY', icon: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z M12 8v4M12 16h.01' },
]

/** 메인 ⑤: AI가 학생 대신 풀지 않아요 */
export function Principles() {
  return (
    <section className="block" id="principles" style={{ paddingTop: 0 }}>
      <div className="wrap">
        <div className="sec-head reveal">
          <div>
            <p className="eyebrow">Principles</p>
            <h2 style={{ marginTop: 10 }}>AI가 학생 대신<br />풀지 않아요</h2>
          </div>
        </div>
        <div className="principles">
          {ITEMS.map((p) => (
            <div key={p.title} className="pr reveal">
              <span className="ic">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d={p.icon} /></svg>
              </span>
              <h3>{p.title}</h3>
              <p>{p.text}</p>
              <span className="lbl">{p.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
