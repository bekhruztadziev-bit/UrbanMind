import React from 'react'
import { Header } from '../Header/Header'

export function FAQ({ t, setCurrentView, toggleLanguage }) {
  return (
    <div className="app-shell faq-shell">
      <Header
        t={t}
        currentView="faq"
        setCurrentView={setCurrentView}
        toggleLanguage={toggleLanguage}
      />

      <main className="faq-page">
        <p className="faq-intro">{t.faqPageIntro}</p>
        <div className="faq-list">
          {t.faqSections.map((item) => (
            <article key={item.q} className="faq-entry">
              <h3>{item.q}</h3>
              <p>{item.a}</p>
            </article>
          ))}
        </div>
      </main>
    </div>
  )
}
