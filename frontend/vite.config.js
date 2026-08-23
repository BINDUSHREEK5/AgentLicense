import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { nodePolyfills } from 'vite-plugin-node-polyfills'

export default defineConfig({
  plugins: [
    react(),

    nodePolyfills({
      include: ['buffer', 'process'],
      globals: {
        Buffer: true,
        global: true,
        process: true,
      },
    }),
  ],

  define: {
    global: 'globalThis',
  },

  optimizeDeps: {
    include: [
      '@x402/core/client',
      '@x402/fetch',
      '@x402/avm',
      '@x402/avm/exact/client',
    ],
  },
})