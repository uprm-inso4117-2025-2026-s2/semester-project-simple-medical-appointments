import { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
  const [colorBlindMode, setColorBlindMode] = useState(
    () => localStorage.getItem('colorBlindMode') ?? 'normal'
  )

  useEffect(() => {
    document.documentElement.classList.remove('theme-monochromatic')
    if (colorBlindMode === 'monochromatic') {
      document.documentElement.classList.add('theme-monochromatic')
    }
    localStorage.setItem('colorBlindMode', colorBlindMode)
  }, [colorBlindMode])

  return (
    <ThemeContext.Provider value={{ colorBlindMode, setColorBlindMode }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
