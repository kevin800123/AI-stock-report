export function formatApiError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => d?.msg || String(d)).join('；')
  }
  const code = err?.code
  const message = err?.message || ''
  if (code === 'ECONNABORTED' || /timeout/i.test(message)) {
    return '連線逾時，後端可能正在啟動，請稍候再試'
  }
  if (code === 'ERR_NETWORK' || !err?.response) {
    return '無法連線後端，請確認網路或稍後再試'
  }
  if (err?.response?.status === 409) {
    return typeof detail === 'string' ? detail : '此檔案已存在或正在處理中'
  }
  return message || '發生未知錯誤，請稍後再試'
}
