import { useCallback, useEffect, useMemo, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { AlertCircle, CheckCircle2, FileUp, Loader2, RefreshCw, Trash2, XCircle } from 'lucide-react'

import { deleteReport, getReports, uploadReport } from '../api.js'

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
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [hint, setHint] = useState('')
  const [deletingId, setDeletingId] = useState(null)

  const fetchReports = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getReports()
      setReports(data || [])
      setError('')
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || '無法取得報告列表')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const init = setTimeout(() => {
      fetchReports()
    }, 0)
    const t = setInterval(fetchReports, 5000)
    return () => {
      clearTimeout(init)
      clearInterval(t)
    }
  }, [fetchReports])

  const onDrop = useCallback(
    async (acceptedFiles) => {
      const file = acceptedFiles?.[0]
      if (!file) return
      setUploading(true)
      setHint('')
      try {
        await uploadReport(file)
        setHint('已上傳，正在背景解析與摘要中...')
        await fetchReports()
      } catch (e) {
        setError(e?.response?.data?.detail || e?.message || '上傳失敗')
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
        await fetchReports()
      } catch (e) {
        setError(e?.response?.data?.detail || e?.message || '刪除失敗')
      } finally {
        setDeletingId(null)
      }
    },
    [fetchReports],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
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
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5 shadow-sm">
          <div className="text-xs text-zinc-400">總報告</div>
          <div className="mt-1 text-2xl font-semibold">{stats.total}</div>
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5 shadow-sm">
          <div className="text-xs text-zinc-400">已完成</div>
          <div className="mt-1 flex items-center gap-2 text-2xl font-semibold">
            <span>{stats.completed}</span>
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          </div>
        </div>
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5 shadow-sm">
          <div className="text-xs text-zinc-400">錯誤</div>
          <div className="mt-1 flex items-center gap-2 text-2xl font-semibold">
            <span>{stats.errorCount}</span>
            <XCircle className="h-5 w-5 text-red-400" />
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold">上傳投顧報告（PDF）</h2>
            <p className="mt-1 text-sm text-zinc-400">
              拖曳 PDF 到下方或點擊選檔，上傳後將自動解析、AI 摘要並寫入 Notion（若已設定）。
            </p>
          </div>
          <button
            type="button"
            onClick={fetchReports}
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-900"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            重新整理
          </button>
        </div>

        <div
          {...getRootProps()}
          className={`mt-5 cursor-pointer rounded-2xl border border-dashed p-8 text-center transition ${
            isDragActive
              ? 'border-indigo-400/60 bg-indigo-500/10'
              : 'border-zinc-700/70 bg-zinc-950/30 hover:bg-zinc-950/50'
          } ${uploading ? 'cursor-not-allowed opacity-70' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-indigo-500/15 text-indigo-300 ring-1 ring-indigo-500/25">
            {uploading ? <Loader2 className="h-6 w-6 animate-spin" /> : <FileUp className="h-6 w-6" />}
          </div>
          <div className="mt-4 text-sm">
            {uploading ? (
              <span className="text-zinc-200">上傳中...</span>
            ) : isDragActive ? (
              <span className="text-indigo-200">放開以開始上傳</span>
            ) : (
              <span className="text-zinc-200">拖曳 PDF 到此處，或點擊選擇檔案</span>
            )}
          </div>
          <div className="mt-1 text-xs text-zinc-500">僅支援 .pdf，單檔上傳</div>
        </div>

        {hint ? (
          <div className="mt-4 inline-flex items-center gap-2 rounded-xl bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200 ring-1 ring-emerald-500/20">
            <CheckCircle2 className="h-4 w-4" />
            {hint}
          </div>
        ) : null}

        {error ? (
          <div className="mt-4 inline-flex items-center gap-2 rounded-xl bg-red-500/10 px-3 py-2 text-sm text-red-200 ring-1 ring-red-500/20">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        ) : null}
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-base font-semibold">報告列表</h2>
          <div className="text-xs text-zinc-500">每 5 秒自動更新狀態</div>
        </div>

        <div className="mt-4 overflow-hidden rounded-2xl border border-zinc-800">
          <table className="w-full text-left text-sm">
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
              {reports.length === 0 ? (
                <tr>
                  <td className="px-4 py-6 text-center text-zinc-500" colSpan={6}>
                    尚無報告，先上傳一份 PDF 吧。
                  </td>
                </tr>
              ) : (
                reports.map((r) => (
                  <tr key={r.id} className="bg-zinc-900/10">
                    <td className="px-4 py-3 max-w-[200px] sm:max-w-[300px] md:max-w-[400px]">
                      <div className="flex items-start gap-2">
                        <FileUp className="h-4 w-4 shrink-0 text-zinc-500 mt-0.5" />
                        <div className="min-w-0">
                          <div className="truncate font-medium text-zinc-100">{r.original_filename}</div>
                          {r.error_message ? (
                            <div className="mt-1 whitespace-normal break-words text-xs text-red-300">
                              {r.error_message}
                            </div>
                          ) : null}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-4 py-3 text-zinc-300">{r.category || '-'}</td>
                    <td className="px-4 py-3 text-zinc-300">{r.stock_tickers || '-'}</td>
                    <td className="px-4 py-3 text-zinc-500">
                      {r.created_at ? new Date(r.created_at).toLocaleString() : '-'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleDelete(r)}
                        disabled={deletingId === r.id}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-red-500/30 bg-red-500/10 px-2.5 py-1.5 text-xs text-red-200 hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-50"
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
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-3 text-xs text-zinc-500">
          狀態含意：Parsing（解析 PDF）、Summarizing（AI 摘要）、Notion（寫入中）、Completed（完成）、Error（失敗）。
        </div>
      </section>
    </div>
  )
}

