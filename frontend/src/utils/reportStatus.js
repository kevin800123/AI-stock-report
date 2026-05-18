export const PROCESSING_STATUSES = new Set([
  'uploading',
  'parsing',
  'summarizing',
  'writing_notion',
])

export function isProcessingReport(report) {
  const s = (report?.status || '').toLowerCase()
  return PROCESSING_STATUSES.has(s)
}

export function hasProcessingReports(reports) {
  return (reports || []).some(isProcessingReport)
}

export function statusStepLabel(status) {
  const s = (status || '').toLowerCase()
  const labels = {
    uploading: '上傳中…',
    parsing: '解析 PDF…',
    summarizing: 'AI 摘要中…',
    writing_notion: '寫入 Notion…',
    completed: '已完成',
    error: '處理失敗',
  }
  return labels[s] || status || '未知狀態'
}

export function elapsedSeconds(createdAt) {
  if (!createdAt) return 0
  const t = new Date(createdAt).getTime()
  if (Number.isNaN(t)) return 0
  return Math.max(0, Math.floor((Date.now() - t) / 1000))
}

/** 舊資料可能仍為技術錯誤句，前端再簡化顯示 */
export function formatReportErrorMessage(msg) {
  if (!msg || typeof msg !== 'string') return msg
  const m = msg.trim()
  if (/GEMINI|NOTION|\.env|API.?KEY|backend\//i.test(m)) {
    return '處理失敗，請稍後重試或重新上傳'
  }
  if (/FileNotFound|找不到檔案/i.test(m)) {
    return '找不到報告檔案，請重新上傳'
  }
  if (/PDF 無法解析|無法解析出任何文字/i.test(m)) {
    return '無法讀取 PDF 內容，請確認檔案是否損壞'
  }
  return m
}
