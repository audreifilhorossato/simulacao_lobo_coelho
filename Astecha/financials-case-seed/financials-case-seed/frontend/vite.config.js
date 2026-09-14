import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// O proxy faz o frontend chamar `/api/...` no MESMO host, o que evita CORS no
// desenvolvimento e mantem os caminhos identicos aos de producao. Nao coloque
// `http://localhost:8000` fixo nos services: na Astecha o backend nao esta
// nesse endereco.
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
