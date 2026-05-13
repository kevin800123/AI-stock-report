import axios from 'axios'

// 本機開發：預設連 localhost。正式／GitHub Pages 建置時請設 VITE_API_BASE_URL（指向已上線的 FastAPI）
const apiBase =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '')

const api = axios.create({
  baseURL: apiBase,
  timeout: 30000,
})

export function getReports() {
  return api.get('/reports/').then((r) => r.data)
}

export function uploadReport(file) {
  const form = new FormData()
  form.append('file', file)
  return api
    .post('/reports/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)
}

export function deleteReport(id) {
  return api.delete(`/reports/${id}`).then(() => undefined)
}

export function getSettings() {
  return api.get('/settings/').then((r) => r.data)
}

export default api

