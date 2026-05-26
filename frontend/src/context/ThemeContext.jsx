import { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext(null)

const COLORBLIND_CLASSES = {
  normal:      null,
  deuteranopia: 'theme-deuteranopia',
  monochromatic: 'theme-monochromatic',
  //Add other colorblind themes here 
}

export function ThemeProvider({ children }) {
  const [highContrast, setHighContrast] = useState(
    () => localStorage.getItem('highContrast') === 'true'
  )

  const [colorBlindMode, setColorBlindMode] = useState(
    () => {
      const saved = localStorage.getItem('colorBlindMode')
      return saved && saved in COLORBLIND_CLASSES ? saved : 'normal'
    }
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
    document.documentElement.classList.remove('theme-protanopia')
    // Add the selected theme
    if (colorBlindMode === 'monochromatic') {
      document.documentElement.classList.add('theme-monochromatic')
    } else if (colorBlindMode === 'protanopia') {
      document.documentElement.classList.add('theme-protanopia')
    Object.values(COLORBLIND_CLASSES).forEach(cls => {
      if (cls) document.documentElement.classList.remove(cls)
    })

    const activeClass = COLORBLIND_CLASSES[colorBlindMode]
    if (activeClass) {
      document.documentElement.classList.add(activeClass)
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
