import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App'
import { ApiError } from './api/client'
import './styles/tokens.css'
import './styles/base.css'
import './styles/components.css'
import './styles/screens.css'
import './styles/layout.css'
import './styles/pages.css'

// 4xx(권한 · 상태 · 입력 오류)는 다시 시도해도 같으므로 바로 보여 준다. 네트워크 · 5xx만 3번까지 재시도
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: (count, err) => !(err instanceof ApiError && err.status < 500) && count < 3 },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
