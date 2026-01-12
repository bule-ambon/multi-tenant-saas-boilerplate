import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    strictPort: true,
    hmr: {
      protocol: 'wss',
      host: '192.168.4.53',
      clientPort: 443,
    },
  },
})
