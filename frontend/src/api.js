import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
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

