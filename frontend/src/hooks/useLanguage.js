import { useState, useMemo } from 'react'
import en from '../locales/en.json'
import ru from '../locales/ru.json'

const translations = {
  en,
  ru
}

export function useLanguage(initialLanguage = 'en') {
  const [language, setLanguage] = useState(initialLanguage)

  const t = useMemo(() => translations[language], [language])

  const toggleLanguage = () => {
    setLanguage((prev) => (prev === 'en' ? 'ru' : 'en'))
  }

  return { language, setLanguage, toggleLanguage, t }
}
