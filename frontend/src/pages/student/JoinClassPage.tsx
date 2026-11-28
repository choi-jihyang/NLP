import { useSearchParams } from 'react-router-dom'

import { PageHead } from '../../components/PageHead'
import JoinFlow from './JoinFlow'

/** 수업 입장 화면: 수업 코드 + 학번 → (명단에 없으면) 참여 요청 대기 → 기록 안내 동의 */
export default function JoinClassPage() {
  const [params] = useSearchParams()
  const expired = params.get('expired') === '1'
  return (
    <>
      <PageHead eyebrow="Join" title="수업 입장" sub="교수자가 알려준 수업 코드를 입력하세요" />
      <main className="wrap page stack">
        {expired && <div className="status wait" role="status">입장이 풀렸어요. 수업 코드와 학번을 다시 입력해 주세요.</div>}
        <JoinFlow />
      </main>
    </>
  )
}
