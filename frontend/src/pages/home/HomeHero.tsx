import { Link } from 'react-router-dom'

/** 히어로: "AI와 함께 스스로 생각하는 과제" */
export function HomeHero() {
  return (
    <section className="hero">
      <div className="wrap hero-in">
        <span className="badge reveal"><b>NEW</b> C 과제 코드 실행 채점</span>
        <h1 className="reveal d1">
          AI와 함께
          <br />
          <span className="self"><span>스</span><span>스</span><span>로</span></span> 생각하는 과제
        </h1>
        <p className="lead reveal d2">
          프로그래밍 과제에서 완성 코드 대신 다음 한 단계를 받고, 과제가 끝나면 AI 없이 내 코드를 설명해요.
        </p>
        <div className="ctas reveal d3">
          <Link className="btn accent lg" to="/signup">교수자로 시작하기</Link>
          <Link className="btn lg" to="/student/join">수업 코드로 입장</Link>
        </div>
      </div>
      <div className="scroll-hint" aria-hidden="true">SCROLL<i /></div>
    </section>
  )
}
