# 📈 投顧報告 AI 分析助理 (AI Investment Report Assistant)

這是一個基於 **React + FastAPI** 打造的高級投資輔助工具，旨在將繁雜的 PDF 投顧報告自動化轉化為專業、結構化的 Notion 投資資料庫。

## ✨ 核心特色

- **🧠 雙模 AI 智慧解析**：整合 Google Gemini 2.0 Flash 尖端模型，自動辨識報告中的評價方法（PER 或 PBR），並精準萃取未來年度 (Forecast Year) 的關鍵估值數據。
- **📊 即時行情聯動**：串接 `yfinance` API，自動抓取台灣股市最新成交價，計算最真實的「潛在漲幅」。
- **📝 Notion 專業儀表板**：自動將摘要同步至 Notion 資料庫，支援自定義欄位如「評價倍數」、「預估目標價」、「風險標籤」等，實現個人化投顧回顧。
- **🚀 專業估值邏輯**：
    - **PER (本益比)**：自動對應預估 EPS 與 PE 倍數。
    - **PBR (股價淨值比)**：自動對應每股淨值 (BVPS) 與 P/B 倍數，特別適合分析半導體、面板與金融類股。
- **🔍 溯源驗證系統**：AI 會優先根據報告中的「目標價」反向溯源計算基礎，確保數據不再與報告打架。

## 🛠️ 系統架構

- **前端**：React + Vite + Tailwind CSS (使用 Lucide 圖標庫)
- **後端**：Python FastAPI
- **AI 核心**：Google Gemini 2.0 Flash API
- **數據源**：Yahoo Finance (yfinance)
- **同步終端**：Notion API (Official SDK)
- **資料庫**：本機 SQLite；雲端建議 PostgreSQL（環境變數 `DATABASE_URL`）

## 📂 專案結構

```
AI投顧報告整理App/
├── frontend/                 # React 前端介面
│   └── src/
│       ├── pages/            # Dashboard, Summary, Settings
│       └── api.js            # API 通訊模組
├── backend/                  # FastAPI 後端服務
│   ├── app/
│   │   ├── services/         # 核心邏輯 (report_processor, notion_service)
│   │   ├── models/           # 數據模型
│   │   └── routers/          # API 路由
│   └── data/                 # SQLite 資料庫與上傳檔案存放區
├── render.yaml               # Render Blueprint（後端 Web Service）
├── start_all.bat             # Windows 一鍵啟動腳本
└── README.md
```

## 🚀 快速啟動

### 1. 環境設定
在 `backend/` 目錄下建立 `.env` 檔案，並填入以下資訊：

```env
GEMINI_API_KEY=您的Gemini金鑰
NOTION_API_KEY=您的Notion金鑰
NOTION_DATABASE_ID=您的Notion資料庫ID
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
```

### 2. 安裝與執行
最簡單的方式是直接執行根目錄下的啟動腳本：

- **Windows**: 點擊 `start_all.bat`
- **macOS/Linux**: `bash start_all.sh`

啟動後，瀏覽器會自動開啟前端介面（預設為 `http://localhost:5173`）。

## 📝 使用流程

1. **設定金鑰**：至「系統設定」頁面確認 Notion 與 AI 金鑰已正確設定。
2. **上傳報告**：在首頁將 PDF 報告拖入上傳區。
3. **AI 分析**：系統會自動完成 `解析 PDF` -> `AI 摘要` -> `即時股價對比`。
4. **自動同步**：完成後，摘要將自動推送到您的 Notion 資料庫中，並建立美觀的分析卡片。

## 🌐 部署到 GitHub Pages + Render（建議流程）

整體順序：**先把後端上架 Render 並取得網址** → **再在 GitHub 設定 Secret 並觸發前端部署**。

### 一、後端：Render

1. 將程式推到 GitHub 後，至 [Render](https://dashboard.render.com) → **New** → **Blueprint**（或 **Web Service** 手動建立）。
2. 若用 Blueprint：選擇此 repo，Render 會讀取根目錄 `render.yaml`。
3. 在 Render 後台的 **Environment** 設定（Blueprint 會提示你填）：
   - **`GEMINI_API_KEY`**、**`NOTION_API_KEY`**、**`NOTION_DATABASE_ID`**：與本機 `backend/.env` 相同。
   - **`DATABASE_URL`（強烈建議）**：在 Render 建立 **PostgreSQL**，於資料庫頁複製 **Internal Database URL**（`postgresql://…`）貼到 Web Service 的環境變數。程式會自動改為 `postgresql+asyncpg://`。
     - 若不設 `DATABASE_URL`，服務會退回容器內 SQLite，**免費方案重啟後資料可能消失**，僅適合試用。
4. 部署完成後記下後端網址，例如 **`https://ai-invest-report-api.onrender.com`**。開啟 **`https://…/health`** 應回傳 `{"status":"ok"}`。
   - 免費 Web 服務休眠後**第一次請求會較慢**，屬正常現象。

### 二、前端：GitHub Pages

1. 在 GitHub Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**：
   - 名稱：**`VITE_API_BASE_URL`**
   - 值：**`https://你的服務.onrender.com`**（**不要**結尾 `/`，且建議 `https`）。
2. 推送程式到 **`main`** 或 **`master`**（或到 **Actions** 手動執行 **Deploy to GitHub Pages**）。
3. Repo → **Settings** → **Pages**：**Build and deployment** → **Deploy from a branch** → 選 **`gh-pages`**、資料夾 **`/(root)`**。
4. 完成後前端網址為：**`https://<GitHub 使用者>.github.io/<儲存庫名稱>/`**  
   若 repo 名為 **`<使用者>.github.io`**，workflow 會用根路徑，網址為 **`https://<使用者>.github.io/`**。

### 三、環境變數對照

| 位置 | 變數 | 說明 |
|------|------|------|
| Render Web Service | `GEMINI_API_KEY`, `NOTION_*`, `DATABASE_URL` | 後端執行與持久化 |
| GitHub Actions Secret | `VITE_API_BASE_URL` | 建置前端時寫入 API 根網址（指向 Render） |

後端已允許 **`https://*.github.io`** 的 CORS。

### 四、Render 部署失敗（Exited with status 1）

常見原因：

1. **缺少依賴**：請確認 `requirements.txt` 含 `yfinance`（報告處理會 `import yfinance`）。若日誌為 `ModuleNotFoundError: No module named 'yfinance'`，拉最新程式後重新部署。
2. **PostgreSQL 連不上**：確認 Web Service 的 **`DATABASE_URL`** 為同一帳號 Postgres 的 **Internal**，或 External URL 且可從網路連線；必要時檢查 Render 該次 deploy 的 **Logs** 內 `asyncpg` / `connection refused` 訊息。

---
*本專案僅供學術與效率提升使用，投資有風險，報告數據僅供參考。*
