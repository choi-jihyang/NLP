import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { HomeNav } from '../home/HomeNav'
import JoinFlow from '../student/JoinFlow'
import LoginForm from './LoginForm'
import SignupForm from './SignupForm'

type Props = { tab: 'login' | 'signup' }

const PLANS = ['SMALL', 'MEDIUM', 'LARGE']

/** 로그인 화면: 교수자(로그인 · 계정 만들기) / 학생(수업 코드 + 학번)을 탭으로. 메인 요금제에서 오면(?plan=) 끝난 뒤 그 요금제로 클래스 개설 */
export default function AuthPage({ tab }: Props) {
  const navigate = useNavigate()
  const { search } = useLocation()
  const [params, setParams] = useSearchParams()
  const plan = params.get('plan')
  const student = params.get('as') === 'student'
  const expired = params.get('expired') === '1'
  const done = () => navigate(plan && PLANS.includes(plan) ? `/teacher/classes/new?plan=${plan}` : '/teacher/classes')
  const go = (t: Props['tab']) => navigate(`/${t}${search}`, { replace: true })
  const setRole = (s: boolean) =>
    setParams((p) => {
      if (s) p.set('as', 'student')
      else p.delete('as')
      return p
    }, { replace: true })

  return (
    <>
      <HomeNav />
      <main className="auth-center">
        <div className="panel stack auth-card">
          {expired && <div className="status wait" role="status">로그인이 풀렸어요. 다시 로그인해 주세요.</div>}
          <div className="seg" role="tablist" aria-label="누구로 들어가나요">
            <button type="button" role="tab" aria-pressed={!student} onClick={() => setRole(false)}>교수자</button>
            <button type="button" role="tab" aria-pressed={student} onClick={() => setRole(true)}>학생</button>
          </div>
          {student ? (
            <>
              <h2>수업 입장</h2>
              <JoinFlow framed={false} onApproved={(classId) => navigate(`/student/consent?class=${classId}`)} />
            </>
          ) : (
            <>
              <div className="seg" role="tablist" aria-label="교수자">
                <button type="button" role="tab" aria-pressed={tab === 'login'} onClick={() => go('login')}>로그인</button>
                <button type="button" role="tab" aria-pressed={tab === 'signup'} onClick={() => go('signup')}>계정 만들기</button>
              </div>
              {tab === 'login' ? <LoginForm onDone={done} /> : <SignupForm onDone={done} />}
            </>
          )}
        </div>
      </main>
    </>
  )
}
