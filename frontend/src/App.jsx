import { NavLink, Route, Routes } from 'react-router-dom'

import Dashboard from './pages/Dashboard.jsx'
import SummaryView from './pages/SummaryView.jsx'

function App() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="sticky top-0 z-10 border-b border-zinc-800/60 bg-zinc-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-500/15 text-indigo-300 ring-1 ring-indigo-400/25">
              AI
            </div>
            <div>
              <div className="text-sm font-semibold leading-tight">投顧報告 AI 分析助理</div>
              <div className="text-xs text-zinc-400">上傳、摘要、Notion 同步</div>
            </div>
          </div>
          <nav className="flex items-center gap-2 text-sm">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 transition ${
                  isActive ? 'bg-zinc-800 text-zinc-50' : 'text-zinc-300 hover:bg-zinc-900'
                }`
              }
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/summary"
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 transition ${
                  isActive ? 'bg-zinc-800 text-zinc-50' : 'text-zinc-300 hover:bg-zinc-900'
                }`
              }
            >
              摘要預覽
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/summary" element={<SummaryView />} />
        </Routes>
      </main>

      <footer className="border-t border-zinc-800/60 py-8">
        <div className="mx-auto max-w-6xl px-4 text-xs text-zinc-500">
          後端預設：<span className="font-mono">http://localhost:8000</span>・前端輪詢每 5 秒更新狀態
        </div>
      </footer>
    </div>
  )
}

export default App
