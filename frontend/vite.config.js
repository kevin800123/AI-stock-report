import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// GitHub Pages 專案站路徑通常為 /<repo-name>/，請於建置時設定環境變數 VITE_BASE（見 .github/workflows）
const base = process.env.VITE_BASE ?? '/'

// https://vite.dev/config/
export default defineConfig({
  base,
  plugins: [react()],
})
