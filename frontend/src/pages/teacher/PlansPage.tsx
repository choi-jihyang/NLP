import { PagePlaceholder } from '../../components/PagePlaceholder'

export default function PlansPage() {
  return (
    <PagePlaceholder
      title="요금제 선택"
      features={[
        'Starter / Pro / Master 비교',
        '학생 수 기준 클래스 단위 결제 (목업, 실제 PG 연동 없음)',
        '개설 후 최대 1년, 연장 시 추가 결제',
      ]}
    />
  )
}
