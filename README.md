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
- **📱 手機友善**：首頁報告列表在小螢幕改為卡片版面，頂部導覽與按鈕加大觸控區，並保留瀏海機安全區（safe area）。
- **🔗 Notion 捷徑**：「摘要預覽」頁提供 **開啟 Notion** 按鈕，新分頁開啟設定的資料庫／頁面（使用 `rel="noopener noreferrer"`）。實際網址常數位於 `frontend/src/pages/SummaryView.jsx`（`NOTION_INDEX_URL`），可依需求自行替換。

## 🛠️ 系統架構

- **前端**：React + Vite + Tailwind CSS（Lucide 圖標）
- **後端**：Python FastAPI
- **AI 核心**：Google Gemini 2.5 Flash API
- **數據源**：Yahoo Finance (yfinance)
- **同步終端**：Notion API (Official SDK)
- **資料庫**：本機 SQLite；雲端建議 PostgreSQL（環境變數 `DATABASE_URL`）

## 📂 專案結構

```
投顧報告整理App/
├── frontend/
│   ├── src/
│   │   ├── pages/           # Dashboard, Summary
│   │   └── api.js
│   └── .env.example
├── backend/
│   ├── app/
│   │   ├── services/        # report_processor, notion_service
│   │   ├── models/
│   │   └── routers/
│   └── data/                # 本機 SQLite 與上傳 PDF（勿提交）
├── .github/
│   └── workflows/
│       └── deploy-gh-pages.yml   # 建置前端並推送 gh-pages
├── render.yaml              # Render Blueprint（後端）
├── start_all.bat / start_all.sh
└── README.md
```

## 🚀 本機快速啟動

### 1. 環境設定

在 `backend/` 下建立 `.env`（可複製 `backend/.env.example`），**勿將 `.env` 提交到 Git**。

```env
GEMINI_API_KEY=您的Gemini金鑰
NOTION_API_KEY=您的Notion金鑰
NOTION_DATABASE_ID=您的Notion資料庫ID
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
```

### 2. 安裝與執行

- **Windows**：執行 `start_all.bat`
- **macOS/Linux**：`bash start_all.sh`

前端預設 `http://localhost:5173`，後端 `http://127.0.0.1:8000`。

### 3. 前端環境變數（選填）

見 `frontend/.env.example`：`VITE_API_BASE_URL`（連遠端 API）、`VITE_API_TIMEOUT_MS`（逾時毫秒，預設本機 30s、正式建置 120s）。

---

## 📝 使用流程

1. **金鑰**：Notion / Gemini 置於 `backend/.env`（或後端平台的環境變數）。
2. **上傳**：Dashboard 上傳 PDF；**Render 免費方案休眠**時可先按 **「叫醒後端」**（呼叫 `/health`）再操作。
3. **流程**：解析 PDF → AI 摘要 →（可選）寫入 Notion。
4. **摘要預覽**：completed 的報告可在「摘要預覽」檢視；可按 **開啟 Notion** 跳到你在程式中設定的 Notion 頁面，與後端同步寫入的資料庫分開設定亦可。
5. **UX**：相同 PDF（SHA-256）若已分析完成會回傳 409 拒絕重複上傳；前端僅在有報告處理中時每 5 秒輪詢更新列表。

## 📓 Notion 資料庫：報告日期與同股排序

- **報告日期**：首次同步時若資料庫尚無對應欄位，程式會嘗試建立 **「報告日期」**（`date`）；寫入 PDF 解析出的發布日（若你的欄位名稱不同，可在 `backend/.env` 設 `NOTION_PROPERTY_REPORT_DATE`）。
- **股票代號欄位**：建議維持為 **文字／rich_text**。系統會將 AI 輸出正規為 **「代號 空格 名稱」**（例如：`2330 台積電`）；若模型另提供 `stock_code` / `stock_name` 會優先組合成此格式，並嘗試將舊式 `飛捷(6206)`、`8299 TT Phison` 等轉成一致寫法。
- **同家公司多篇報告上下排列**：Notion API **無法指定列的絕對順序**，請在該資料表的「…」→ **Layout / 群組與排序** 中：
  1. （建議）依 **「股票代號」** 群組；  
  2. 再以 **「報告日期」遞減** 排序，**日期較新的一列會排在上方**（同一群組內）。  
  若未群組，至少要設 **依「報告日期」遞減** 排序。

---

## 🌐 部署：GitHub Pages + Render

順序建議：**後端 Render 可連線** → **GitHub Secret `VITE_API_BASE_URL`** → **觸發前端 workflow**。

### 後端（Render）

1. 將 repo 推到 GitHub，至 [Render](https://dashboard.render.com) → **Blueprint** 或 **Web Service**，對應根目錄 `render.yaml` 或手動指定 `backend`、`uvicorn app.main:app --host 0.0.0.0 --port $PORT`。
2. **環境變數**：`GEMINI_API_KEY`、`NOTION_API_KEY`、`NOTION_DATABASE_ID`；上傳防護 **`UPLOAD_API_KEY`**（隨機長字串）、**`REQUIRE_UPLOAD_API_KEY=true`**（見 `render.yaml`）；**強烈建議**另建 **PostgreSQL**，將 **Internal Database URL** 設為 `DATABASE_URL`。
3. 部署後測試：`https://你的服務.onrender.com/health` → `{"status":"ok"}`。
4. **免費 Web Service** 閒置會休眠，**首次請求常需數十秒**；須穩定低延遲請升級方案。

### 前端（GitHub Pages）

1. **Repository secret**（Actions）：**`VITE_API_BASE_URL`** = `https://你的服務.onrender.com`（**無結尾斜線**）；**`VITE_UPLOAD_API_KEY`** = 與 Render 上 `UPLOAD_API_KEY` **相同**（供上傳／刪除帶 `X-API-Key`）。
2. Push 到 `main` 或手動執行 workflow **Deploy to GitHub Pages**。
3. **Settings → Pages**：
   - **免費帳號**：私有 repo **無法**使用 Pages，請改為 **Public**，或升級 GitHub Pro。
   - **本專案**使用 peaceiris 將靜態檔推到 **`gh-pages` 分支**，請選 **Deploy from a branch** → Branch **`gh-pages`** / **`/(root)`**。（若只顯示「GitHub Actions」為來源，請改為 **Deploy from a branch** 並選 `gh-pages`，與本倉 workflow 一致。）
4. 網址：`https://<使用者>.github.io/<儲存庫名>/`（使用者網站 repo `<使用者>.github.io` 則為根路徑）。

### CI 與 lock 檔

GitHub Actions 使用 **`npm ci`**，請在本機變更依賴後執行 **`npm install`**（於 `frontend/`），並**一併提交** `package-lock.json`，否則建置會失敗。

### 環境變數對照

| 位置 | 變數 | 說明 |
|------|------|------|
| Render Web Service | `GEMINI_API_KEY`, `NOTION_*`, `DATABASE_URL`, `UPLOAD_API_KEY`, `REQUIRE_UPLOAD_API_KEY` | 後端、資料庫與上傳閘門 |
| GitHub Actions Secret | `VITE_API_BASE_URL`, `VITE_UPLOAD_API_KEY` | 建置前端時嵌入 API 網址與上傳 key |

後端 CORS 僅允許 **`https://kevin800123.github.io`**（你的 GitHub Pages Origin；本機 `localhost` / `127.0.0.1` 亦在允許清單）。

### 常見問題

| 問題 | 處理 |
|------|------|
| 前端 `timeout` / 逾時 | 正式站 Axios 預設 **120s**；冷啟動仍慢時先按 **叫醒後端** 或手動開 `/health`。 |
| Render `Exited with status 1` | 確認 `requirements.txt` 含 **`yfinance`**；檢查 Postgres **`DATABASE_URL`** 與 Logs。 |
| `npm ci` 與 lock 不同步 | 於 `frontend/` 執行 `npm install` 後提交 `package-lock.json`。 |

---

## 🔒 資安與隱私（簡述）

- **API 網址**：瀏覽器本來就會向後端發請求，**網址無法對使用者完全隱藏**；頁尾 **僅在開發模式 (`npm run dev`)** 顯示 API 字樣，正式站不顯示，但開發者工具仍可能看到請求目標。
- **金鑰**：Gemini / Notion 等**僅能放後端環境變數**（或本機 `backend/.env`），**不要**寫進公開 repo。
- **上傳 API key**：`POST /reports/upload` 與 `DELETE /reports/{id}` 需 `X-API-Key`（10MB 上限、PDF magic bytes、上傳 **5 次/分鐘/IP**）。正式站前端透過 `VITE_UPLOAD_API_KEY` 帶入——**打包後仍可被檢視**，僅能擋不知道 key 的隨機濫用，無法取代登入或後端代傳；請定期輪替 key 並監控 Render／Gemini 用量。
- **投顧 PDF**：**禁止**提交至 Git（`backend/data/reports/` 僅供本機上傳目錄，已列入 `.gitignore`）。若曾誤傳至公開 repo，需以 `git filter-repo` 等工具清除整段 history 後 force push；並可向 [GitHub Support](https://support.github.com/contact) 申請清除舊 commit 的快取。
- **摘要頁 Notion 連結**：捷徑網址寫在前端原始碼中，打包後仍可被檢視。若 Notion 頁面設為「知道連結的任何人」可讀／可編輯，等同對能開啟你網站的人暴露該權限；請以 Notion 的分享範圍與成員權限控管。連結僅為瀏覽器導向 `https://www.notion.so/...`，不經後端代理，無 SSRF 問題。

---

*本專案僅供學術與效率提升使用，投資有風險，報告數據僅供參考。*
