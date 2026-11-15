import { PagePlaceholder } from '../../components/PagePlaceholder'

export default function SolvePage() {
  return (
    <PagePlaceholder
      title="과제 풀이"
      features={[
        '왼쪽 문항 / 오른쪽 학습 AI 채팅',
        '혼자 푼 문항은 제출 전 개념 확인 질문',
        '붙여넣기 기록 (길이·시점만)',
        'AI 사용량 상한 도달 시 안내',
      ]}
    />
  )
}
