import { PagePlaceholder } from '../../components/PagePlaceholder'

export default function ClassListPage() {
  return (
    <PagePlaceholder
      title="내 클래스"
      features={[
        '클래스 목록 (과목명, 학생 수/상한, 만료일)',
        '클래스 개설 버튼',
      ]}
    />
  )
}
