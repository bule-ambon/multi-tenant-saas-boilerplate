import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const parsePort = (value: string | undefined, fallback?: number): number | undefined => {
  if (!value) {
    return fallback
  }

  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

const hmrHost = process.env.VITE_HMR_HOST
const hmrPort = parsePort(process.env.VITE_HMR_PORT, 3000)
const hmrClientPort = parsePort(process.env.VITE_HMR_CLIENT_PORT, hmrPort)
const hmrProtocol = process.env.VITE_HMR_PROTOCOL ?? 'wss'

const hmrConfig = hmrHost
  ? {
      protocol: hmrProtocol,
      host: hmrHost,
      port: hmrPort,
      clientPort: hmrClientPort,
    }
  : undefined

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    strictPort: true,
    hmr: hmrConfig,
  },
})
