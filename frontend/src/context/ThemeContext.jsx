import { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
  const [highContrast, setHighContrast] = useState(
    () => localStorage.getItem('highContrast') === 'true'
  )

  const [colorBlindMode, setColorBlindMode] = useState(
    () => localStorage.getItem('colorBlindMode') ?? 'normal'
  )

  useEffect(() => {
    if (highContrast) {
      document.documentElement.classList.add('theme-high-contrast')
    } else {
      document.documentElement.classList.remove('theme-high-contrast')
    }
    localStorage.setItem('highContrast', highContrast)
  }, [highContrast])

  useEffect(() => {
    document.documentElement.classList.remove('theme-monochromatic')
    if (colorBlindMode === 'monochromatic') {
      document.documentElement.classList.add('theme-monochromatic')
    }
    localStorage.setItem('colorBlindMode', colorBlindMode)
  }, [colorBlindMode])

  return (
    <ThemeContext.Provider value={{ highContrast, setHighContrast, colorBlindMode, setColorBlindMode }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
