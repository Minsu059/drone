import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // dev: 프론트(5173)에서 /api/* 호출 → FastAPI(8000)로 프록시
    // 빌드 후에는 FastAPI가 정적 자산까지 같은 호스트에서 서빙하므로 프록시 불필요
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: false,
      },
    },
  },
})
