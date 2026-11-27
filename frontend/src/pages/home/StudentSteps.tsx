const STEPS = [
  ['입장', '수업 코드 + 학번. 기록 열람·붙여넣기 기록 안내에 동의해요.'],
  ['풀기', '문항 옆 AI에게 물어봐요. 내가 시도한 만큼 힌트가 열려요.'],
  ['제출', '혼자 푼 문항은 쓴 개념을 하나 짚고, 문항을 다 내면 최종 제출.'],
  ['이해 확인', 'AI 없이 내 코드를 설명하고, 공개되면 내 리포트를 봐요.'],
]

/** 메인 ④: 학생 흐름 4단계 */
export function StudentSteps() {
  return (
    <section className="block" id="student">
      <div className="wrap">
        <div className="sec-head reveal">
          <div>
            <p className="eyebrow">For students</p>
            <h2 style={{ marginTop: 10 }}>가입 없이,<br />수업 코드와 학번으로</h2>
          </div>
          <p className="muted">학생은 무료예요. 교수자가 알려준 수업 코드만 있으면 바로 과제를 풀 수 있어요.</p>
        </div>
        <div className="hsteps">
          {STEPS.map(([title, text]) => (
            <div key={title} className="hstep"><h3>{title}</h3><p>{text}</p></div>
          ))}
        </div>
      </div>
    </section>
  )
}
