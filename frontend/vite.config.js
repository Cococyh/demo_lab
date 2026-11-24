import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  // 開発用サーバー（npm run dev）で /api を後端（5000）へ中継する。本番のビルドには影響しない
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5000',
    },
  },
})
