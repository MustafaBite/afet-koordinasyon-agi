import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  
  server: {
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:8000', // localhost yerine 127.0.0.1 kullandık
        changeOrigin: true,
        // EĞER PYTHON TARAFINDA ADRES SADECE "/login" İSE ŞU SATIRIN BAŞINDAKİ // İŞARETLERİNİ KALDIR:
        // rewrite: (path) => path.replace(/^\/auth/, '')
      },
      '/talepler': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/requests': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/buyuk-depremler': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
