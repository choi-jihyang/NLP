import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { HomeNav } from '../home/HomeNav'
import LoginForm from './LoginForm'
import SignupForm from './SignupForm'

type Props = { tab: 'login' | 'signup' }

const PLANS = ['SMALL', 'MEDIUM', 'LARGE']

/** 로그인 / 계정 만들기를 한 화면의 탭으로. 메인 요금제에서 오면(?plan=) 끝난 뒤 그 요금제로 클래스 개설 */
export default function AuthPage({ tab }: Props) {
  const navigate = useNavigate()
  const { search } = useLocation()
  const [params] = useSearchParams()
  const plan = params.get('plan')
  const expired = params.get('expired') === '1'
  const done = () => navigate(plan && PLANS.includes(plan) ? `/teacher/classes/new?plan=${plan}` : '/teacher/classes')
  const go = (t: Props['tab']) => navigate(`/${t}${search}`, { replace: true })

  return (
    <>
      <HomeNav />
      <main className="auth-center">
        <div className="panel stack auth-card">
          {expired && <div className="status wait" role="status">로그인이 풀렸어요. 다시 로그인해 주세요.</div>}
          <div className="seg" role="tablist">
            <button type="button" role="tab" aria-pressed={tab === 'login'} onClick={() => go('login')}>로그인</button>
            <button type="button" role="tab" aria-pressed={tab === 'signup'} onClick={() => go('signup')}>계정 만들기</button>
          </div>
          {tab === 'login' ? <LoginForm onDone={done} /> : <SignupForm onDone={done} />}
          <hr className="sep" />
          <p className="note">
            학생은 계정 없이 <Link to="/student/join">수업 코드로 입장</Link>해요.
          </p>
        </div>
      </main>
    </>
  )
}
