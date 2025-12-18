import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/health': 'http://localhost:8000',
      '/telemetry': 'http://localhost:8000',
      '/facility-ceiling': 'http://localhost:8000',
      '/facility-grid': 'http://localhost:8000',
      '/scenarios': 'http://localhost:8000',
    },
  },
})
