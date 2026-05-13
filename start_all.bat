@echo off
chcp 65001 >nul
setlocal

set ROOT=%~dp0

echo ============================================
echo   投顧報告 AI 分析助理 - 啟動全端開發環境
echo ============================================
echo.

echo [Backend] 啟動 FastAPI (http://localhost:8000)
start "Backend - FastAPI" cmd /k "cd /d %ROOT%backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak >nul

echo [Frontend] 啟動 Vite Dev Server (http://localhost:5173)
start "Frontend - Vite" cmd /k "cd /d %ROOT%frontend && npm run dev"

echo.
echo 已開啟兩個視窗分別執行前端與後端。
echo 關閉對應視窗即可停止服務。
endlocal
