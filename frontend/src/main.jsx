// Entry point of the React application.
// This file mounts the root <App /> component into the #root div in index.html.
import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css' // Global styles
import './styles/themes.css' // Accessibility themes (monochromatic, etc.)

const isSlotUsagePreview = window.location.pathname === '/slot-usage-preview'
const AppShell = React.lazy(() => import('./ShellApp'))
const SlotUsagePreview = React.lazy(() => import('./pages/SlotUsagePreview'))

function RootApp() {
  return isSlotUsagePreview ? <SlotUsagePreview /> : <AppShell />
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <React.Suspense fallback={<main style={{ padding: '2rem' }}>Loading preview...</main>}>
      <RootApp />
    </React.Suspense>
  </React.StrictMode>
)
