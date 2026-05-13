import { useEffect, useMemo, useState } from 'react'
import { BadgeCheck, FileText, RefreshCw, Tag } from 'lucide-react'

import { getReports } from '../api.js'

function Badge({ children, tone = 'zinc' }) {
  const tones = {
    zinc: 'bg-zinc-800 text-zinc-200 ring-zinc-700',
    indigo: 'bg-indigo-500/15 text-indigo-300 ring-indigo-500/25',
    emerald: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/25',
    amber: 'bg-amber-500/15 text-amber-300 ring-amber-500/25',
  }
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs ring-1 ${tones[tone]}`}>
      {children}
    </span>
  )
}

export default function SummaryView() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function fetchReports() {
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
  }

  useEffect(() => {
    const t = setTimeout(() => {
      fetchReports()
    }, 0)
    return () => clearTimeout(t)
  }, [])

  const completed = useMemo(
    () => reports.filter((r) => (r.status || '').toLowerCase() === 'completed'),
    [reports],
  )

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold">摘要預覽</h2>
            <p className="mt-1 text-sm text-zinc-400">
              只顯示狀態為 <span className="font-semibold text-zinc-200">completed</span> 的報告。
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

        {error ? <div className="mt-4 text-sm text-red-300">{error}</div> : null}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        {completed.length === 0 ? (
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-8 text-center text-sm text-zinc-400 shadow-sm md:col-span-2">
            目前沒有已完成的摘要。請先到 Dashboard 上傳 PDF。
          </div>
        ) : (
          completed.map((r) => (
            <article key={r.id} className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-sm text-zinc-400">
                    <FileText className="h-4 w-4" />
                    <span className="truncate">{r.original_filename}</span>
                  </div>
                  <h3 className="mt-2 line-clamp-2 text-base font-semibold text-zinc-100">
                    {r.category ? r.category : '未分類'}
                  </h3>
                </div>
                <Badge tone="emerald">
                  <BadgeCheck className="h-3.5 w-3.5" />
                  completed
                </Badge>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {r.category ? (
                  <Badge tone="indigo">
                    <Tag className="h-3.5 w-3.5" />
                    {r.category}
                  </Badge>
                ) : (
                  <Badge>未分類</Badge>
                )}
                {r.stock_tickers ? <Badge tone="amber">{r.stock_tickers}</Badge> : <Badge>未提供代號</Badge>}
              </div>

              <div className="mt-4 whitespace-pre-line text-sm leading-relaxed text-zinc-200">
                {r.summary || '（尚無摘要內容）'}
              </div>

              {r.error_message ? <div className="mt-4 text-sm text-red-300">{r.error_message}</div> : null}

              <div className="mt-5 text-xs text-zinc-500">
                {r.created_at ? `建立時間：${new Date(r.created_at).toLocaleString()}` : null}
                {r.notion_page_id ? ` ・ Notion Page: ${r.notion_page_id}` : null}
              </div>
            </article>
          ))
        )}
      </section>
    </div>
  )
}

