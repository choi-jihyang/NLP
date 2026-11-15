import { PagePlaceholder } from '../../components/PagePlaceholder'

export default function SignupPage() {
  return (
    <PagePlaceholder
      title="회원가입"
      features={[
        '이름·이메일·비밀번호',
        '역할 선택: 교수자 / 학생',
      ]}
    />
  )
}
