import { PageHead } from '../../components/PageHead'
import JoinFlow from './JoinFlow'

/** 수업 입장 화면: 수업 코드 + 학번 → (명단에 없으면) 참여 요청 대기 → 기록 안내 동의 */
export default function JoinClassPage() {
  return (
    <>
      <PageHead eyebrow="Join" title="수업 입장" sub="교수자가 알려준 수업 코드를 입력하세요" />
      <main className="wrap page">
        <JoinFlow />
      </main>
    </>
  )
}
