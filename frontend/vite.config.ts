import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    // /api 요청은 FastAPI로 전달 → 개발 중 CORS 신경 쓸 필요 없음
    // 8000 포트를 다른 프로그램이 쓰고 있으면: API_PROXY_TARGET=http://localhost:8010 npm run dev
    proxy: {
      '/api': process.env.API_PROXY_TARGET ?? 'http://localhost:8000',
    },
  },
})
