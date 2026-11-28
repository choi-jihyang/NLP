import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { logout } from '../api/auth'

/** 로그아웃: 토큰 · 다시 입장 티켓 · 화면이 기억한 서버 데이터(내 클래스 목록 등)를 지우고 메인으로 */
export function useLogout(): () => void {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  return () => {
    logout()
    navigate('/')
    queryClient.clear()
  }
}
