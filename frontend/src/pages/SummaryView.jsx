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
    <div className="space-y-5 sm:space-y-6">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 shadow-sm sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <h2 className="text-base font-semibold">摘要預覽</h2>
            <p className="mt-1 text-sm leading-relaxed text-zinc-400">
              只顯示狀態為 <span className="font-semibold text-zinc-200">completed</span> 的報告。
            </p>
          </div>
          <button
            type="button"
            onClick={fetchReports}
            className="inline-flex min-h-[44px] w-full shrink-0 touch-manipulation items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2.5 text-sm text-zinc-200 hover:bg-zinc-900 active:bg-zinc-800 sm:w-auto"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            重新整理
          </button>
        </div>

        {error ? <div className="mt-4 break-words text-sm text-red-300">{error}</div> : null}
      </section>

      <section className="grid gap-3 sm:gap-4 md:grid-cols-2">
        {completed.length === 0 ? (
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 text-center text-sm leading-relaxed text-zinc-400 shadow-sm sm:p-8 md:col-span-2">
            目前沒有已完成的摘要。請先到 Dashboard 上傳 PDF。
          </div>
        ) : (
          completed.map((r) => (
            <article key={r.id} className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 shadow-sm sm:p-6">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex min-w-0 items-center gap-2 text-sm text-zinc-400">
                    <FileText className="h-4 w-4 shrink-0" />
                    <span className="break-words">{r.original_filename}</span>
                  </div>
                  <h3 className="mt-2 line-clamp-3 text-base font-semibold leading-snug text-zinc-100 sm:line-clamp-2">
                    {r.category ? r.category : '未分類'}
                  </h3>
                </div>
                <Badge tone="emerald">
                  <BadgeCheck className="h-3.5 w-3.5 shrink-0" />
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

              <div className="mt-4 break-words whitespace-pre-line text-sm leading-relaxed text-zinc-200">
                {r.summary || '（尚無摘要內容）'}
              </div>

              {r.error_message ? <div className="mt-4 break-words text-sm text-red-300">{r.error_message}</div> : null}

              <div className="mt-5 text-xs leading-relaxed text-zinc-500">
                {r.created_at ? <span className="block sm:inline">建立時間：{new Date(r.created_at).toLocaleString()}</span> : null}
                {r.notion_page_id ? (
                  <span className="mt-1 block break-all sm:mt-0 sm:inline sm:before:content-['・']">
                    Notion：{r.notion_page_id}
                  </span>
                ) : null}
              </div>
            </article>
          ))
        )}
      </section>
    </div>
  )
}

