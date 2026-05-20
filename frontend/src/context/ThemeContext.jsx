import { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
  const [highContrast, setHighContrast] = useState(
    () => localStorage.getItem('highContrast') === 'true'
  )

  useEffect(() => {
    if (highContrast) {
      document.documentElement.classList.add('theme-high-contrast')
    } else {
      document.documentElement.classList.remove('theme-high-contrast')
    }
    localStorage.setItem('highContrast', highContrast)
  }, [highContrast])

  return (
    <ThemeContext.Provider value={{ highContrast, setHighContrast }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
