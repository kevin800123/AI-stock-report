import { useCallback, useEffect, useMemo, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { AlertCircle, CheckCircle2, FileUp, Loader2, RefreshCw, Trash2, XCircle, Zap } from 'lucide-react'

import ReportProgressHint from '../components/ReportProgressHint.jsx'
import { useBackendWakeContext } from '../context/BackendWakeContext.jsx'
import { useReportsPolling } from '../hooks/useReportsPolling.js'
import { deleteReport, uploadReport } from '../api.js'
import { formatApiError } from '../utils/apiErrors.js'
import { formatReportErrorMessage, hasProcessingReports } from '../utils/reportStatus.js'
import { getUploadSizeError, UPLOAD_MAX_BYTES, uploadMaxSizeLabel } from '../uploadLimits.js'

function StatusBadge({ status }) {
  const s = (status || '').toLowerCase()
  const cfg = {
    uploading: { label: 'Uploading', cls: 'bg-zinc-800 text-zinc-200 ring-zinc-700' },
    parsing: { label: 'Parsing', cls: 'bg-blue-500/15 text-blue-300 ring-blue-500/25' },
    summarizing: { label: 'Summarizing', cls: 'bg-violet-500/15 text-violet-300 ring-violet-500/25' },
    writing_notion: { label: 'Notion', cls: 'bg-amber-500/15 text-amber-300 ring-amber-500/25' },
    completed: { label: 'Completed', cls: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/25' },
    error: { label: 'Error', cls: 'bg-red-500/15 text-red-300 ring-red-500/25' },
  }[s] || { label: status || 'Unknown', cls: 'bg-zinc-800 text-zinc-200 ring-zinc-700' }

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs ring-1 ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}

export default function Dashboard() {
  const { reports, loading, error: pollError, refresh, isPolling, fetchReports } = useReportsPolling()
  const { canWakeBackend, wakeBusy, wakeLine, handleWakeBackend } = useBackendWakeContext()
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [hint, setHint] = useState('')
  const [deletingId, setDeletingId] = useState(null)
  const [tick, setTick] = useState(0)

  const displayError = error || pollError

  useEffect(() => {
    if (!hasProcessingReports(reports)) return undefined
    const id = setInterval(() => setTick((n) => n + 1), 1000)
    return () => clearInterval(id)
  }, [reports])

  const onDrop = useCallback(
    async (acceptedFiles) => {
      const file = acceptedFiles?.[0]
      if (!file) return
      const sizeError = getUploadSizeError(file)
      if (sizeError) {
        setError(sizeError)
        setHint('')
        return
      }
      setUploading(true)
      setHint('')
      setError('')
      try {
        await uploadReport(file)
        setHint('已上傳，正在背景解析與摘要中...')
        await fetchReports({ silent: true })
      } catch (e) {
        setError(formatApiError(e))
      } finally {
        setUploading(false)
      }
    },
    [fetchReports],
  )

  const handleDelete = useCallback(
    async (r) => {
      const name = r?.original_filename || '此報告'
      if (!window.confirm(`確定要刪除「${name}」嗎？此動作無法復原。`)) return
      setDeletingId(r.id)
      setError('')
      try {
        await deleteReport(r.id)
        await fetchReports({ silent: true })
      } catch (e) {
        setError(formatApiError(e))
      } finally {
        setDeletingId(null)
      }
    },
    [fetchReports],
  )

  const onWakeClick = useCallback(async () => {
    setError('')
    try {
      await handleWakeBackend()
    } catch (e) {
      setError(formatApiError(e))
    }
  }, [handleWakeBackend])

  const onDropRejected = useCallback((rejections) => {
    const tooLarge = rejections.some((r) =>
      r.errors.some((e) => e.code === 'file-too-large'),
    )
    if (tooLarge) {
      setError(`檔案超過大小上限（${uploadMaxSizeLabel()}）`)
      setHint('')
      return
    }
    setError('僅支援單一 PDF 檔案')
    setHint('')
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDropRejected,
    accept: { 'application/pdf': ['.pdf'] },
    maxSize: UPLOAD_MAX_BYTES,
    multiple: false,
    disabled: uploading,
  })

  const stats = useMemo(() => {
    const total = reports.length
    const completed = reports.filter((r) => (r.status || '').toLowerCase() === 'completed').length
    const errorCount = reports.filter((r) => (r.status || '').toLowerCase() === 'error').length
    return { total, completed, errorCount }
  }, [reports])

  return (
    <div className="space-y-5 sm:space-y-6">
      <section className="grid grid-cols-3 gap-2 sm:gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-3 shadow-sm sm:p-5">
          <div className="text-[11px] text-zinc-400 sm:text-xs">總報告</div>
          <div className="mt-0.5 text-xl font-semibold tabular-nums sm:mt-1 sm:text-2xl">{stats.total}</div>
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-3 shadow-sm sm:p-5">
          <div className="text-[11px] text-zinc-400 sm:text-xs">已完成</div>
          <div className="mt-0.5 flex items-center gap-1.5 text-xl font-semibold tabular-nums sm:mt-1 sm:gap-2 sm:text-2xl">
            <span>{stats.completed}</span>
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400 sm:h-5 sm:w-5" />
          </div>
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-3 shadow-sm sm:p-5">
          <div className="text-[11px] text-zinc-400 sm:text-xs">錯誤</div>
          <div className="mt-0.5 flex items-center gap-1.5 text-xl font-semibold tabular-nums sm:mt-1 sm:gap-2 sm:text-2xl">
            <span>{stats.errorCount}</span>
            <XCircle className="h-4 w-4 shrink-0 text-red-400 sm:h-5 sm:w-5" />
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 shadow-sm sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <h2 className="text-base font-semibold">上傳投顧報告（PDF）</h2>
            <p className="mt-1 text-sm leading-relaxed text-zinc-400">
              拖曳 PDF 到下方或點擊選檔，上傳後將自動解析、AI 摘要並寫入 Notion（若已設定）。
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:flex sm:w-auto sm:flex-row sm:flex-wrap sm:justify-end">
            <button
              type="button"
              onClick={onWakeClick}
              disabled={!canWakeBackend || wakeBusy}
              title={
                canWakeBackend
                  ? '先打一次健康檢查，喚醒休眠中的 Render 免費主機（第一次可能需 1～2 分鐘）'
                  : '請先設定 VITE_API_BASE_URL 並重新部署'
              }
              className="inline-flex min-h-[44px] touch-manipulation items-center justify-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2.5 text-sm text-amber-100 hover:bg-amber-500/15 active:bg-amber-500/20 disabled:cursor-not-allowed disabled:opacity-50 sm:min-w-0"
            >
              {wakeBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
              叫醒後端
            </button>
            <button
              type="button"
              onClick={refresh}
              className="inline-flex min-h-[44px] touch-manipulation items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2.5 text-sm text-zinc-200 hover:bg-zinc-900 active:bg-zinc-800 sm:w-auto"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              重新整理
            </button>
          </div>
        </div>

        {wakeLine ? (
          <div className="mt-3 flex w-full max-w-full items-start gap-2 rounded-xl bg-sky-500/10 px-3 py-2.5 text-sm leading-relaxed text-sky-200 ring-1 ring-sky-500/20">
            <Zap className="h-4 w-4 shrink-0 pt-0.5" />
            <span className="min-w-0 break-words">{wakeLine}</span>
          </div>
        ) : null}

        <div
          {...getRootProps()}
          className={`mt-4 touch-manipulation cursor-pointer rounded-2xl border border-dashed p-6 text-center transition sm:mt-5 sm:p-8 ${
            isDragActive
              ? 'border-indigo-400/60 bg-indigo-500/10'
              : 'border-zinc-700/70 bg-zinc-950/30 active:bg-zinc-950/50 sm:hover:bg-zinc-950/50'
          } ${uploading ? 'cursor-not-allowed opacity-70' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-indigo-500/15 text-indigo-300 ring-1 ring-indigo-500/25">
            {uploading ? <Loader2 className="h-6 w-6 animate-spin" /> : <FileUp className="h-6 w-6" />}
          </div>
          <div className="mt-3 text-sm sm:mt-4">
            {uploading ? (
              <span className="text-zinc-200">上傳中...</span>
            ) : isDragActive ? (
              <span className="text-indigo-200">放開以開始上傳</span>
            ) : (
              <span className="text-zinc-200">點擊選擇 PDF（手機可由此挑檔）</span>
            )}
          </div>
          <div className="mt-1 hidden text-xs text-zinc-500 sm:block">亦支援拖曳 PDF 到此處</div>
          <div className="mt-1 text-xs text-zinc-500">僅支援 .pdf，單檔上傳，上限 {uploadMaxSizeLabel()}</div>
        </div>

        {hint ? (
          <div className="mt-3 flex w-full max-w-full items-start gap-2 rounded-xl bg-emerald-500/10 px-3 py-2.5 text-sm leading-relaxed text-emerald-200 ring-1 ring-emerald-500/20 sm:mt-4">
            <CheckCircle2 className="h-4 w-4 shrink-0 pt-0.5" />
            <span className="min-w-0 break-words">{hint}</span>
          </div>
        ) : null}

        {error ? (
          <div className="mt-3 flex w-full max-w-full items-start gap-2 rounded-xl bg-red-500/10 px-3 py-2.5 text-sm leading-relaxed text-red-200 ring-1 ring-red-500/20 sm:mt-4">
            <AlertCircle className="h-4 w-4 shrink-0 pt-0.5" />
            <span className="min-w-0 break-words">{displayError}</span>
          </div>
        ) : null}
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 shadow-sm sm:p-6">
        <div className="flex flex-col gap-1 gap-y-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-base font-semibold">報告列表</h2>
          <div className="text-xs text-zinc-500">
            {isPolling ? '處理中：每 5 秒自動更新' : '全部完成，已停止自動更新'}
          </div>
        </div>

        {reports.length === 0 ? (
          <div className="mt-4 rounded-2xl border border-zinc-800 py-10 text-center text-sm text-zinc-500">
            尚無報告，先上傳一份 PDF 吧。
          </div>
        ) : (
          <>
            <div className="mt-4 space-y-3 md:hidden">
              {reports.map((r) => (
                <div
                  key={r.id}
                  className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex min-w-0 flex-1 items-start gap-2">
                      <FileUp className="h-4 w-4 shrink-0 text-zinc-500" />
                      <div className="min-w-0">
                        <div className="break-words font-medium text-zinc-100">{r.original_filename}</div>
                        <ReportProgressHint report={r} tick={tick} />
                        {r.error_message ? (
                          <div className="mt-2 break-words text-xs text-red-300">{formatReportErrorMessage(r.error_message)}</div>
                        ) : null}
                      </div>
                    </div>
                    <StatusBadge status={r.status} />
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-zinc-400">
                    <div>
                      <span className="text-zinc-600">類別</span>
                      <div className="mt-0.5 text-zinc-300">{r.category || '-'}</div>
                    </div>
                    <div>
                      <span className="text-zinc-600">代號</span>
                      <div className="mt-0.5 break-all text-zinc-300">{r.stock_tickers || '-'}</div>
                    </div>
                    <div className="col-span-2">
                      <span className="text-zinc-600">時間</span>
                      <div className="mt-0.5 text-zinc-500">
                        {r.created_at ? new Date(r.created_at).toLocaleString() : '-'}
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 flex justify-end">
                    <button
                      type="button"
                      onClick={() => handleDelete(r)}
                      disabled={deletingId === r.id}
                      className="inline-flex min-h-[44px] min-w-[88px] touch-manipulation items-center justify-center gap-1.5 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200 hover:bg-red-500/20 active:bg-red-500/25 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {deletingId === r.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                      刪除
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 hidden overflow-x-auto rounded-2xl border border-zinc-800 md:block">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="bg-zinc-950/40 text-xs text-zinc-400">
                  <tr>
                    <th className="px-4 py-3 font-medium">檔名</th>
                    <th className="px-4 py-3 font-medium">狀態</th>
                    <th className="px-4 py-3 font-medium">類別</th>
                    <th className="px-4 py-3 font-medium">股票代號</th>
                    <th className="px-4 py-3 font-medium">時間</th>
                    <th className="px-4 py-3 font-medium text-right">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {reports.map((r) => (
                    <tr key={r.id} className="bg-zinc-900/10">
                      <td className="max-w-[12rem] px-4 py-3 lg:max-w-[18rem] xl:max-w-md">
                        <div className="flex items-start gap-2">
                          <FileUp className="mt-0.5 h-4 w-4 shrink-0 text-zinc-500" />
                          <div className="min-w-0">
                            <div className="font-medium text-zinc-100">{r.original_filename}</div>
                            <ReportProgressHint report={r} tick={tick} />
                            {r.error_message ? (
                              <div className="mt-1 whitespace-normal break-words text-xs text-red-300">
                                {formatReportErrorMessage(r.error_message)}
                              </div>
                            ) : null}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="space-y-1">
                          <StatusBadge status={r.status} />
                          <ReportProgressHint report={r} tick={tick} />
                        </div>
                      </td>
                      <td className="px-4 py-3 text-zinc-300">{r.category || '-'}</td>
                      <td className="break-all px-4 py-3 text-zinc-300">{r.stock_tickers || '-'}</td>
                      <td className="whitespace-nowrap px-4 py-3 text-zinc-500">
                        {r.created_at ? new Date(r.created_at).toLocaleString() : '-'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => handleDelete(r)}
                          disabled={deletingId === r.id}
                          className="inline-flex min-h-[36px] touch-manipulation items-center gap-1.5 rounded-lg border border-red-500/30 bg-red-500/10 px-2.5 py-1.5 text-xs text-red-200 hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                          title="刪除此報告"
                        >
                          {deletingId === r.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                          )}
                          刪除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        <div className="mt-3 text-xs leading-relaxed text-zinc-500">
          狀態：Parsing（解析）→ Summarizing（AI）→ Notion → Completed；Error（失敗）。
        </div>
      </section>
    </div>
  )
}

