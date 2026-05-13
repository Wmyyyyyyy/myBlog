import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import OpenAPI from 'vite-plugin-openapi'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue(),
    OpenAPI({
      target: 'http://localhost:8000',
      output: './src/api/generated',
      client: 'axios',
      exportSchemas: true,
      watch: true,
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
