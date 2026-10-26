import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    // Built straight into the Python package so the wheel ships the GUI.
    outDir: '../scim_sanity/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
