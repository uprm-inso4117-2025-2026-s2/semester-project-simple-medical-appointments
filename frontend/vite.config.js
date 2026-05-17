// Vite configuration file — controls the dev server and build settings.
// Vite is the tool that runs `npm run dev` and `npm run build`.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // Registers the React plugin so Vite understands JSX and fast-refresh
  plugins: [react()],

  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
  },

  server: {
    // The port the React dev server listens on
    port: 3000,

    // Proxy: any request starting with /api is forwarded to the Flask backend.
    // This lets the frontend call fetch('/api/...') without CORS issues during development.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // Flask runs here
        changeOrigin: true,              // Rewrites the Host header to match the target
      },
    },
  },
})
