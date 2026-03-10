// Entry point of the React application.
// This file mounts the root <App /> component into the #root div in index.html.
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css' // Global styles

ReactDOM.createRoot(document.getElementById('root')).render(
  // StrictMode highlights potential issues in development (double-renders, deprecated APIs, etc.)
  <React.StrictMode>
    {/* BrowserRouter enables client-side routing using the browser's URL bar */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
