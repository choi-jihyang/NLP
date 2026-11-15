import { PagePlaceholder } from '../../components/PagePlaceholder'

export default function AiSettingsPage() {
  return (
    <PagePlaceholder
      title="학습 AI 설정"
      features={[
        '과목 유형: 수학 / 프로그래밍 / 글쓰기 / 개념 학습',
        '힌트 제공 여부, 최대 힌트 단계 수',
        '유형별 기본 정책 (선택형, 프롬프트 직접 입력 없음)',
      ]}
    />
  )
}
