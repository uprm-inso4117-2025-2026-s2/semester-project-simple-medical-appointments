// Entry point of the React application.
// This file mounts the root <App /> component into the #root div in index.html.
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css' // Global styles
import './styles/themes.css' // Accessibility themes (high-contrast, colorblind, etc.)

import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'

ReactDOM.createRoot(document.getElementById('root')).render(

  // AuthProvider wraps the entire app to provide authentication context
  <AuthProvider>
    {/* ThemeProvider reads persisted theme from localStorage and applies it */}
    <ThemeProvider>
      {/* StrictMode highlights potential issues in development (double-renders, deprecated APIs, etc.) */}
      <React.StrictMode>
        {/* BrowserRouter enables client-side routing using the browser's URL bar */}
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </React.StrictMode>
    </ThemeProvider>
  </AuthProvider>
)
