import { Link } from 'react-router-dom'

import { Logo } from '../../components/layout/Logo'

/** 메인 마무리 버튼 + 푸터 */
export function HomeFooter() {
  return (
    <>
      <section className="final">
        <div className="wrap reveal">
          <h2>AI와 함께<br />스스로 생각하는 과제</h2>
          <div className="ctas">
            <Link className="btn accent lg" to="/signup">교수자로 시작하기</Link>
            <Link className="btn lg" to="/student/join">수업 코드로 입장</Link>
          </div>
        </div>
      </section>
      <footer>
        <div className="wrap">
          <div className="fgrid">
            <div>
              <Logo to="/" />
              <p className="muted" style={{ marginTop: 12, fontSize: '.9rem' }}>프로그래밍 과제용 학습 AI 튜터</p>
            </div>
            <div><h4>교수자</h4><ul><li><Link to="/login">로그인</Link></li><li><Link to="/signup">계정 만들기</Link></li><li><a href="#start">요금제</a></li></ul></div>
            <div><h4>학생</h4><ul><li><Link to="/student/join">수업 코드로 입장</Link></li><li><Link to="/student/classes">내 과제</Link></li></ul></div>
            <div><h4>안내</h4><ul><li><a href="#principles">원칙</a></li></ul></div>
          </div>
          <div className="fbottom"><span>© 2026 ThinkGuard · 자연언어처리 수업 팀 프로젝트</span></div>
        </div>
      </footer>
    </>
  )
}
