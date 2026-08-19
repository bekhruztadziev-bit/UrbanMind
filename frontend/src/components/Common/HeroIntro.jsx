import React, { useState, useEffect } from 'react'

export function HeroIntro({ t, language, setLanguage, toggleLanguage, isOpen, onClose, onSelectView }) {
  const [dontShowAgain, setDontShowAgain] = useState(false)
  const isRu = language === 'ru'

  useEffect(() => {
    const saved = localStorage.getItem('urbanmind_hide_intro')
    if (saved === 'true') {
      setDontShowAgain(true)
    }
  }, [])

  const handleClose = () => {
    if (dontShowAgain) {
      localStorage.setItem('urbanmind_hide_intro', 'true')
    } else {
      localStorage.removeItem('urbanmind_hide_intro')
    }
    onClose()
  }

  const handleCardClick = (view) => {
    if (dontShowAgain) {
      localStorage.setItem('urbanmind_hide_intro', 'true')
    }
    onSelectView(view)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="hero-intro-overlay" onClick={handleClose}>
      <div className="hero-intro-modal" onClick={(e) => e.stopPropagation()}>
        {/* Top Control Bar with Language Switcher and Close Button */}
        <div className="hero-intro-topbar">
          <div className="hero-lang-switch">
            <button
              type="button"
              className={`hero-lang-btn ${language === 'ru' ? 'active' : ''}`}
              onClick={() => {
                if (setLanguage) setLanguage('ru')
                else if (language !== 'ru' && toggleLanguage) toggleLanguage()
              }}
            >
              🇷🇺 RU
            </button>
            <button
              type="button"
              className={`hero-lang-btn ${language === 'en' ? 'active' : ''}`}
              onClick={() => {
                if (setLanguage) setLanguage('en')
                else if (language !== 'en' && toggleLanguage) toggleLanguage()
              }}
            >
              🇬🇧 EN
            </button>
          </div>

          <button type="button" className="hero-intro-close" onClick={handleClose} aria-label="Close intro">
            ✕
          </button>
        </div>

        {/* Brand Glow Logo */}
        <div className="hero-intro-header">
          <div className="hero-logo-badge">
            <span className="hero-logo-symbol">U</span>
            <div className="hero-logo-glow" />
          </div>
          <h1 className="hero-title">URBANMIND</h1>
          <p className="hero-subtitle">
            {t.introSubtitle || (isRu ? 'Цифровой двойник и интеллектуальная оптимизация городской мобильности' : 'Neighborhood Mobility Intelligence & Urban Digital Twin')}
          </p>
          <p className="hero-desc">
            {t.introDesc || (isRu ? 'Платформа моделирования транспортных потоков, фаз светофоров и экологических факторов на основе реальной физики SUMO и ИИ-аналитики.' : 'Traffic flow simulation, signal timing optimization, and environmental monitoring powered by SUMO physics and multi-objective Gemini AI.')}
          </p>
        </div>

        {/* Feature Highlights Grid */}
        <div className="hero-feature-grid">
          <div className="hero-feature-card" onClick={() => handleCardClick('insights')}>
            <div className="hero-card-icon signal-icon">🚦</div>
            <div className="hero-card-content">
              <h3>{isRu ? 'Панель светофоров' : 'Live Signal Dashboard'}</h3>
              <p>{isRu ? 'Оперативная оптимизация фаз, устранение заторов на перекрестках и расчет задержек транспорта.' : 'Real-time signal timing optimization, bottleneck resolution, and delay reduction.'}</p>
            </div>
            <span className="hero-card-arrow">→</span>
          </div>

          <div className="hero-feature-card" onClick={() => handleCardClick('explore')}>
            <div className="hero-card-icon lab-icon">🧪</div>
            <div className="hero-card-content">
              <h3>{isRu ? 'Среда «Что если»' : 'What-If Scenario Lab'}</h3>
              <p>{isRu ? 'Стресс-тестирование при 0.8×–1.4× нагрузке, сравнение автобусных полос и пешеходных окон.' : 'Multi-condition stress testing across 0.8×–1.4× traffic demand and transit priority.'}</p>
            </div>
            <span className="hero-card-arrow">→</span>
          </div>

          <div className="hero-feature-card" onClick={() => handleCardClick('faq')}>
            <div className="hero-card-icon data-icon">📊</div>
            <div className="hero-card-content">
              <h3>{isRu ? 'Методология и FAQ' : 'Insights & Methodology'}</h3>
              <p>{isRu ? 'Многокритериальная оценка мобильности, экологические показатели и научно обоснованный выбор мер.' : 'Multi-objective mobility metrics, environmental sensing, and explainable AI reasoning.'}</p>
            </div>
            <span className="hero-card-arrow">→</span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="hero-intro-footer">
          <label className="hero-checkbox-label">
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.target.checked)}
            />
            <span>{t.introDontShow || (isRu ? 'Не показывать заставку при входе' : "Don't show this screen on startup")}</span>
          </label>

          <button type="button" className="hero-launch-btn" onClick={handleClose}>
            {t.introLaunch || (isRu ? 'Войти в платформу →' : 'Launch Platform →')}
          </button>
        </div>
      </div>
    </div>
  )
}
