import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react(), tailwindcss()],
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
    server: {
      strictPort: true,
      proxy: {
        '/monitoring-api': {
          target: env.DASHBOARD_MONITORING_UPSTREAM || 'http://127.0.0.1:8010',
          rewrite: (p) => p.replace(/^\/monitoring-api/, ''),
        },
        '/security-api': {
          target: env.DASHBOARD_SECURITY_UPSTREAM || 'http://127.0.0.1:8020',
          rewrite: (p) => p.replace(/^\/security-api/, ''),
        },
      },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./src/test/setup.ts'],
      exclude: ['e2e/**', 'node_modules/**'],
    },
  }
})
