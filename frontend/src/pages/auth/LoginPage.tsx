import { PagePlaceholder } from '../../components/PagePlaceholder'

export default function LoginPage() {
  return (
    <PagePlaceholder
      title="로그인"
      features={[
        '이메일·비밀번호 로그인',
        '역할(교수자/학생)에 따라 첫 화면 이동',
      ]}
    />
  )
}
