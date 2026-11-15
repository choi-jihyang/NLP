import { PagePlaceholder } from '../../components/PagePlaceholder'

export default function DashboardPage() {
  return (
    <PagePlaceholder
      title="반 전체 분석"
      features={[
        '문항별 오답률',
        '힌트를 많이 쓴 문항',
        '반 전체가 막히는 지점',
        '외부 AI 사용 의심 신호 (참고용)',
      ]}
    />
  )
}
