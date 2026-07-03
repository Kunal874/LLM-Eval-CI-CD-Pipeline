import axios from 'axios'
import type { TestCase, CasesResponse, UploadResponse } from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || ''

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  },
})

// Dataset API
export const casesApi = {
  list: (params?: { category?: string; limit?: number; offset?: number }) =>
    api.get<CasesResponse>('/api/v1/cases', { params }),

  create: (data: { question: string; expected_answer: string; category?: string }) =>
    api.post<TestCase>('/api/v1/cases', data),

  update: (id: string, data: Partial<{ question: string; expected_answer: string; category: string }>) =>
    api.put<TestCase>(`/api/v1/cases/${id}`, data),

  delete: (id: string) =>
    api.delete<{ deleted: boolean }>(`/api/v1/cases/${id}`),

  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<UploadResponse>('/api/v1/cases/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  exportYaml: () =>
    api.get('/api/v1/cases/export/yaml', { responseType: 'blob' }),
}
