import { PagePlaceholder } from '../../components/PagePlaceholder'

export default function ClassDetailPage() {
  return (
    <PagePlaceholder
      title="클래스 상세"
      features={[
        '초대 코드, 참여 학생 목록',
        '과제 목록과 과제 등록',
        'AI 설정·대시보드로 이동',
      ]}
    />
  )
}
