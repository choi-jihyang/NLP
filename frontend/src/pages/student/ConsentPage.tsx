import { useNavigate, useSearchParams } from 'react-router-dom'

import { PageHead } from '../../components/PageHead'
import ConsentCard from './ConsentCard'

/** 다시 입장한 뒤 기록 안내 동의(?class=) */
export default function ConsentPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  return (
    <>
      <PageHead eyebrow="Consent" title="기록 안내" />
      <main className="wrap page">
        <ConsentCard classId={Number(params.get('class'))} onDone={() => navigate('/student/classes')} />
      </main>
    </>
  )
}
