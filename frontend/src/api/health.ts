import { api } from './client'

export type Health = {
  status: 'ok'
  llm_provider: 'mock' | 'ollama'
  classifier: 'stub' | 'module' | 'http'
}

export const getHealth = () => api<Health>('/health')
