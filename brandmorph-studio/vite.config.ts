import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: { host: '0.0.0.0', port: 8443, strictPort: false },
  preview: { host: '0.0.0.0', port: 8443 },
  build: {
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/pptxgenjs') || id.includes('node_modules\\pptxgenjs')) {
            return 'pptx-engine'
          }
          if (id.includes('node_modules/framer-motion') || id.includes('node_modules\\framer-motion')) {
            return 'motion'
          }
        },
      },
    },
  },
})
