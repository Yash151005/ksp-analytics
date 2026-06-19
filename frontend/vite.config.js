import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    },
    headers: {
      'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; img-src 'self' data: https:; font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; connect-src 'self' http://localhost:8000 https://api.ksp-analytics.onslate.in https://cdnjs.cloudflare.com;",
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  }
})
