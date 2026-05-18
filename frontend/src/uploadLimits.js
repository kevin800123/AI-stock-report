/** 與後端 UPLOAD_MAX_BYTES 預設一致（10 MB） */
const DEFAULT_MAX_BYTES = 10 * 1024 * 1024

const parsed = Number(import.meta.env.VITE_UPLOAD_MAX_BYTES)
export const UPLOAD_MAX_BYTES =
  Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_MAX_BYTES

export function uploadMaxSizeLabel() {
  const mb = UPLOAD_MAX_BYTES / (1024 * 1024)
  return Number.isInteger(mb) ? `${mb} MB` : `${mb.toFixed(1)} MB`
}

export function getUploadSizeError(file) {
  if (!file || file.size <= UPLOAD_MAX_BYTES) return null
  return `檔案超過大小上限（${uploadMaxSizeLabel()}）`
}
