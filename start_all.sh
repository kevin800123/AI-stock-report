#!/usr/bin/env bash
# ============================================
#   投顧報告 AI 分析助理 - 啟動全端開發環境
# ============================================

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

cleanup() {
  echo ""
  echo "[*] 收到結束訊號，正在關閉前後端服務..."
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
  echo "[*] 服務已關閉。"
}

trap cleanup EXIT INT TERM

echo "============================================"
echo "  投顧報告 AI 分析助理 - 啟動全端開發環境"
echo "============================================"

# 啟動後端
echo "[Backend] 啟動 FastAPI (http://localhost:8000)"
cd "$BACKEND_DIR"

if [[ -d "venv/Scripts" ]]; then
  # Windows (Git Bash / MSYS)
  PYTHON_BIN="venv/Scripts/python"
elif [[ -d "venv/bin" ]]; then
  PYTHON_BIN="venv/bin/python"
else
  echo "[!] 找不到 backend/venv，請先建立 Python 虛擬環境。"
  exit 1
fi

"$PYTHON_BIN" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

# 啟動前端
echo "[Frontend] 啟動 Vite Dev Server (http://localhost:5173)"
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"
echo "按 Ctrl+C 結束全部服務。"

wait
