import axios from 'axios'

import { getUploadSizeError } from './uploadLimits.js'

// 本機開發：預設連 localhost。正式／GitHub Pages 建置時請設 VITE_API_BASE_URL（指向已上線的 FastAPI）
const apiBase =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '')

// Render 免費方案冷啟動常超過 30s，正式站預設 120s；本機維持 30s。可建置變數 VITE_API_TIMEOUT_MS 覆寫。
const requestTimeout = Number(import.meta.env.VITE_API_TIMEOUT_MS) || (import.meta.env.DEV ? 30000 : 120000)

const uploadApiKey = import.meta.env.VITE_UPLOAD_API_KEY || ''

const api = axios.create({
  baseURL: apiBase,
  timeout: requestTimeout,
  headers: uploadApiKey ? { 'X-API-Key': uploadApiKey } : {},
})

export function getReports() {
  return api.get('/reports/').then((r) => r.data)
}

export function uploadReport(file) {
  const sizeError = getUploadSizeError(file)
  if (sizeError) {
    return Promise.reject(new Error(sizeError))
  }
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

/** 打 /health 觸發冷啟動中的後端開始喚醒（Render 免費方案休眠時很有用） */
export function pingHealth() {
  return api.get('/health').then((r) => r.data)
}

export default api

