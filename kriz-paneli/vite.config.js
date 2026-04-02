import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  
  server: {
    proxy: {
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/talepler': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/requests': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/buyuk-depremler': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
