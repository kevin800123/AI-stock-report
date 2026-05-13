import { NavLink, Route, Routes } from 'react-router-dom'

import Dashboard from './pages/Dashboard.jsx'
import SummaryView from './pages/SummaryView.jsx'

function App() {
  const missingApiUrl = import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL

  return (
    <div className="min-h-screen min-h-[100dvh] bg-zinc-950 text-zinc-100">
      {missingApiUrl ? (
        <div className="border-b border-amber-500/30 bg-amber-500/10 px-3 py-3 text-left text-xs leading-relaxed text-amber-100 sm:px-4 sm:text-center sm:text-sm">
          未設定後端網址：請在 GitHub Repository → Settings → Secrets and variables → Actions 新增{' '}
          <span className="font-mono">VITE_API_BASE_URL</span>（你的 FastAPI 公開網址，勿結尾斜線），並重新執行部署 workflow。
        </div>
      ) : null}
      <header className="sticky top-0 z-20 border-b border-zinc-800/60 bg-zinc-950/90 backdrop-blur pt-[max(0.5rem,env(safe-area-inset-top))]">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-3 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-4 sm:py-4">
          <div className="flex min-w-0 items-center gap-2.5 sm:gap-3">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-indigo-500/15 text-indigo-300 ring-1 ring-indigo-400/25 sm:h-10 sm:w-10">
              AI
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold leading-tight sm:text-base">投顧報告 AI 分析助理</div>
              <div className="hidden text-xs text-zinc-400 sm:block">上傳、摘要、Notion 同步</div>
            </div>
          </div>
          <nav className="flex w-full items-stretch gap-1.5 text-sm sm:w-auto sm:items-center sm:justify-end sm:gap-2">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `flex min-h-[44px] flex-1 touch-manipulation items-center justify-center rounded-lg px-3 py-2.5 transition sm:min-h-0 sm:flex-initial sm:px-3 sm:py-2 ${
                  isActive ? 'bg-zinc-800 text-zinc-50' : 'text-zinc-300 hover:bg-zinc-900 active:bg-zinc-800'
                }`
              }
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/summary"
              className={({ isActive }) =>
                `flex min-h-[44px] flex-1 touch-manipulation items-center justify-center rounded-lg px-3 py-2.5 transition sm:min-h-0 sm:flex-initial sm:px-3 sm:py-2 ${
                  isActive ? 'bg-zinc-800 text-zinc-50' : 'text-zinc-300 hover:bg-zinc-900 active:bg-zinc-800'
                }`
              }
            >
              摘要預覽
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-3 py-5 sm:px-4 sm:py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/summary" element={<SummaryView />} />
        </Routes>
      </main>

      <footer className="border-t border-zinc-800/60 pt-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] sm:pt-8">
        <div className="mx-auto max-w-6xl break-words px-3 text-xs leading-relaxed text-zinc-500 sm:px-4">
          {import.meta.env.DEV ? (
            <>
              <span className="text-zinc-500">API：</span>
              <span className="break-all font-mono text-zinc-400">
                {import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}
              </span>
              <span className="mt-1 block text-zinc-600 sm:mt-0 sm:inline"> ・ </span>
            </>
          ) : null}
          <span className="text-zinc-600">前端輪詢每 5 秒更新狀態</span>
        </div>
      </footer>
    </div>
  )
}

export default App
