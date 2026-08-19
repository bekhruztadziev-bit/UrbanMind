import React from 'react'

export function Header({ t, currentView, setCurrentView, toggleLanguage, onOpenIntro }) {
  const getTitle = () => {
    switch(currentView) {
      case 'faq': return t.faqPageTitle;
      case 'explore': return t.explore;
      case 'history': return t.history;
      case 'insights': return t.headerTitle;
      default: return t.headerTitle;
    }
  }

  return (
    <header className={currentView === 'insights' ? 'map-header' : 'topbar'}>
      <div className="brand-wrap" style={{ cursor: onOpenIntro ? 'pointer' : 'default' }} onClick={onOpenIntro}>
        <div className="brand-mark">U</div>
        <div>
          <p className="eyebrow">{t.appTitle}</p>
          <h1>{getTitle()}</h1>
        </div>
      </div>
      <div className="topbar-actions">
        {onOpenIntro && (
          <button type="button" className="ghost-button intro-btn" onClick={onOpenIntro} title="Open Intro Menu">
            ⚡ {t.introMenu || 'Intro'}
          </button>
        )}
        <button type="button" className={`ghost-button ${currentView === 'insights' ? 'active' : ''}`} onClick={() => setCurrentView('insights')}>{t.insights}</button>
        <button type="button" className={`ghost-button ${currentView === 'explore' ? 'active' : ''}`} onClick={() => setCurrentView('explore')}>{t.explore}</button>
        <button type="button" className={`ghost-button ${currentView === 'history' ? 'active' : ''}`} onClick={() => setCurrentView('history')}>{t.history}</button>
        <button type="button" className={`ghost-button ${currentView === 'faq' ? 'active' : ''}`} onClick={() => setCurrentView('faq')}>{t.faq}</button>
        <button type="button" className="language-toggle" onClick={toggleLanguage}>{t.language}</button>
      </div>
    </header>
  )
}

