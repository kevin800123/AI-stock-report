# 投顧報告 AI 分析助理（全端專案）

以 **React + FastAPI** 打造的全端工具：上傳投顧 PDF，後端解析文字後呼叫 **OpenAI** 產生摘要（強制 JSON 輸出），並可寫入 **Notion Database** 做集中管理。

## 系統架構

- **前端**：React + Vite + Tailwind CSS
  - 主要套件：axios、react-dropzone、lucide-react、react-router-dom
- **後端**：Python FastAPI
  - SQLAlchemy (async) + aiosqlite、PyMuPDF、OpenAI、Notion SDK、python-dotenv
- **資料庫**：SQLite（`backend/data/app.db`）

## 功能模組

- **Dashboard**
  - PDF 拖曳上傳
  - 報告狀態列表（每 5 秒輪詢更新）
- **摘要預覽**
  - 顯示 `completed` 報告的摘要卡片（Badge：產業類別、股票代號）
- **設定**
  - 儲存 Notion Secret / Database ID
  - 後端儲存時會測試 Notion 連線（失敗回 400）

## 專案結構（重點）

```
AI投顧報告整理App/
├── frontend/                         # React + Vite + Tailwind 前端
│   └── src/
│       ├── api.js                    # axios API wrapper（指向 http://localhost:8000）
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── SummaryView.jsx
│       │   └── Settings.jsx
│       ├── App.jsx                   # Router + Layout
│       └── main.jsx                  # BrowserRouter
├── backend/                          # FastAPI 後端
│   ├── app/
│   │   ├── main.py                   # FastAPI + CORS + lifespan 自動建表
│   │   ├── database.py               # Async SQLite engine/session
│   │   ├── models/                   # Report / Setting ORM
│   │   ├── routers/                  # /reports /settings
│   │   └── services/                 # report_processor / notion_service
│   └── data/
│       ├── app.db                    # SQLite DB
│       └── reports/                  # 上傳 PDF 存放
├── start_all.bat                     # Windows 一鍵啟動
├── start_all.sh                      # macOS/Linux/Git Bash 一鍵啟動
└── README.md
```

## 本地啟動（建議先準備 .env）

後端在做 OpenAI 摘要時會讀取 `OPENAI_API_KEY`（也支援把 `openai_api_key` 存在 DB 的 settings）。

在 `backend/` 建立 `.env`：

```bash
cd backend
copy .env.example .env   # Windows
# 或 cp .env.example .env # macOS/Linux
```

並在 `backend/.env` 設定：

```
OPENAI_API_KEY=你的金鑰
```

### 一鍵啟動（推薦）

- **Windows**：

```bat
start_all.bat
```

- **macOS / Linux / Git Bash**：

```bash
chmod +x start_all.sh
./start_all.sh
```

> 注意：Vite 若發現 `5173` 被占用會自動改用 `5174`；後端已允許 `localhost` 其他 port 的 CORS，以避免啟動卡住。

### 分開啟動

後端（預設 `http://localhost:8000`）：

```bash
cd backend
venv\Scripts\activate   # 或 source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端（Vite 預設 `http://localhost:5173`，若占用會跳到 5174）：

```bash
cd frontend
npm run dev
```

## API 文件

- Swagger UI：`http://localhost:8000/docs`

## 使用流程（最短路徑）

1. 啟動前後端
2. 到「設定」頁輸入 Notion Secret 與 Database ID（儲存時會測試連線）
3. 到 Dashboard 上傳 PDF
4. 等待狀態變成 `completed`，到「摘要預覽」查看摘要卡片
