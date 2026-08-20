import React, { useState } from 'react'

export function PolicySelector({
  t = {},
  language = 'en',
  activePolicy = 'balanced',
  onSelectPolicy,
  customWeights = { mobility: 0.34, environment: 0.33, accessibility: 0.33 },
  onUpdateCustomWeights,
  onComparePolicies,
  isComparing = false,
  disabled = false,
}) {
  const isRu = language === 'ru'
  const [showCustomSliders, setShowCustomSliders] = useState(false)

  const POLICIES = [
    {
      id: 'balanced',
      icon: '⚖️',
      name: t.policyBalanced || (isRu ? 'БАЛАНС' : 'BALANCED'),
      question: isRu ? 'Какой вариант обеспечивает наилучший баланс между задержками, экологией и пешеходами?' : 'Which candidate provides the strongest compromise between mobility, environment, and accessibility?',
      desc: t.policyBalancedDesc || (isRu ? 'Многокритериальный баланс: мобильность (45%), экология (35%), безопасность (20%)' : 'Holistic multi-objective balance: mobility (45%), eco (35%), access (20%)'),
      weights: { mobility: 45, environment: 35, accessibility: 20 },
      badge: isRu ? 'Сбалансированный' : 'Multi-Objective',
    },
    {
      id: 'flow',
      icon: '🚗',
      name: t.policyFlow || (isRu ? 'ТРАФИК' : 'FLOW'),
      question: isRu ? 'Какой вариант лучше всего повышает транспортную мобильность и снижает задержки?' : 'Which candidate best improves traffic mobility and minimizes delays?',
      desc: t.policyFlowDesc || (isRu ? 'Приоритет мобильности (80%): минимизация задержек, очередей и времени в пути' : 'Mobility priority (80%): minimize delays, queues, and travel times'),
      weights: { mobility: 80, environment: 10, accessibility: 10 },
      badge: isRu ? 'Приоритет потока' : 'Mobility Priority',
    },
    {
      id: 'eco',
      icon: '🌱',
      name: t.policyEco || (isRu ? 'ЭКО' : 'ECO'),
      question: isRu ? 'Какой вариант лучше всего снижает расчетные выбросы CO₂, NOₓ и холостой ход?' : 'Which candidate best reduces modeled transportation environmental impact?',
      desc: t.policyEcoDesc || (isRu ? 'Приоритет экологии (75%): минимизация выбросов CO₂, NOₓ и холостого хода (SIMULATED)' : 'Environmental priority (75%): minimize simulated CO₂, NOₓ emissions and idling'),
      weights: { mobility: 15, environment: 75, accessibility: 10 },
      badge: isRu ? 'Эко-приоритет' : 'Eco Priority (Simulated)',
    },
    {
      id: 'custom',
      icon: '⚙️',
      name: t.policyCustom || (isRu ? 'НАСТРОЙКА' : 'CUSTOM'),
      question: isRu ? 'Какой вариант лучше всего отвечает заданным муниципальным весам целей?' : 'Which candidate best satisfies user-configured municipal objective weights?',
      desc: t.policyCustomDesc || (isRu ? 'Пользовательские муниципальные веса целей оптимизации' : 'Configurable municipal objective weights'),
      weights: {
        mobility: Math.round((customWeights?.mobility ?? 0.34) * 100),
        environment: Math.round((customWeights?.environment ?? 0.33) * 100),
        accessibility: Math.round((customWeights?.accessibility ?? 0.33) * 100),
      },
      badge: isRu ? 'Настраиваемый' : 'Configurable',
    },
  ]

  const currentPolicy = POLICIES.find(p => p.id === activePolicy) || POLICIES[0]

  const handleSliderChange = (key, val) => {
    if (!onUpdateCustomWeights) return
    const rawVal = Math.max(1, Math.min(100, Number(val)))
    const currentWeights = {
      mobility: (customWeights?.mobility ?? 0.34) * 100,
      environment: (customWeights?.environment ?? 0.33) * 100,
      accessibility: (customWeights?.accessibility ?? 0.33) * 100,
    }
    currentWeights[key] = rawVal
    
    // Normalize so sum is 1.0
    const total = Object.values(currentWeights).reduce((a, b) => a + b, 0)
    const normalized = {
      mobility: Number((currentWeights.mobility / total).toFixed(3)),
      environment: Number((currentWeights.environment / total).toFixed(3)),
      accessibility: Number((currentWeights.accessibility / total).toFixed(3)),
    }
    onUpdateCustomWeights(normalized)
  }

  return (
    <div className="panel-card policy-selector-panel" style={{ padding: '1rem', marginBottom: '1rem', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
      {/* Explicit Decision Prompt Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
        <div>
          <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--accent-primary)', fontWeight: 700, display: 'block' }}>
            {isRu ? 'ЧТО ДОЛЖЕН ПРИОРИТИЗИРОВАТЬ URBANMIND?' : 'WHAT SHOULD URBANMIND PRIORITIZE?'}
          </span>
          <h4 style={{ margin: 0, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
            🎯 {t.optimizationPolicy || (isRu ? 'Целевая политика оптимизации' : 'Optimization Policy Objective')}
          </h4>
        </div>
        
        {onComparePolicies && (
          <button
            type="button"
            className={isComparing ? 'accent' : 'ghost-button'}
            onClick={onComparePolicies}
            style={{ fontSize: '0.76rem', padding: '0.35rem 0.65rem', borderRadius: '6px', fontWeight: 600 }}
          >
            ⚖️ {isRu ? 'Сравнить политики' : 'Compare Policies'}
          </button>
        )}
      </div>

      {/* Policy Pills Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem', marginBottom: '0.65rem' }}>
        {POLICIES.map(p => {
          const isActive = activePolicy === p.id
          return (
            <button
              key={p.id}
              type="button"
              disabled={disabled}
              onClick={() => {
                onSelectPolicy(p.id)
                if (p.id === 'custom') setShowCustomSliders(true)
              }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '0.55rem 0.3rem',
                borderRadius: '8px',
                border: isActive ? '1.5px solid var(--accent-primary)' : '1px solid rgba(255,255,255,0.08)',
                background: isActive ? 'rgba(56, 189, 248, 0.16)' : 'rgba(255,255,255,0.02)',
                color: isActive ? 'var(--accent-primary)' : 'var(--text-primary)',
                fontWeight: isActive ? 700 : 500,
                fontSize: '0.78rem',
                cursor: disabled ? 'not-allowed' : 'pointer',
                transition: 'all 0.18s ease',
              }}
            >
              <span style={{ fontSize: '1.15rem', marginBottom: '2px' }}>{p.icon}</span>
              <span>{p.name}</span>
            </button>
          )
        })}
      </div>

      {/* Active Policy Decision Question & Details */}
      <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.65rem 0.8rem', borderRadius: '6px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '0.35rem' }}>
          <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>❓ {isRu ? 'Вопрос решения:' : 'Decision Question:'}</span>
          <span style={{ color: 'var(--accent-primary)', fontStyle: 'italic' }}>{currentPolicy.question}</span>
        </div>
        <p style={{ margin: '0 0 0.4rem 0', lineHeight: 1.4, color: 'var(--text-muted)' }}>{currentPolicy.desc}</p>
        
        {/* Objective Weight Distribution Bar */}
        <div style={{ display: 'flex', height: '6px', borderRadius: '3px', overflow: 'hidden', background: 'rgba(255,255,255,0.1)', marginBottom: '0.35rem' }}>
          <div style={{ width: `${currentPolicy.weights.mobility}%`, background: '#38bdf8' }} title={`Mobility: ${currentPolicy.weights.mobility}%`} />
          <div style={{ width: `${currentPolicy.weights.environment}%`, background: '#4ade80' }} title={`Environment: ${currentPolicy.weights.environment}%`} />
          <div style={{ width: `${currentPolicy.weights.accessibility}%`, background: '#fbbf24' }} title={`Accessibility: ${currentPolicy.weights.accessibility}%`} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
          <span>🚗 {t.mobility || (isRu ? 'Мобильность' : 'Mobility')}: {currentPolicy.weights.mobility}%</span>
          <span>🌱 {t.environment || (isRu ? 'Экология' : 'Eco')}: {currentPolicy.weights.environment}%</span>
          <span>🚶 {t.accessibility || (isRu ? 'Доступность' : 'Access')}: {currentPolicy.weights.accessibility}%</span>
        </div>
      </div>

      {/* Custom Sliders (if activePolicy === 'custom') */}
      {activePolicy === 'custom' && (
        <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(56, 189, 248, 0.05)', borderRadius: '6px', border: '1px dashed rgba(56, 189, 248, 0.25)' }}>
          <div style={{ display: 'grid', gap: '0.6rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', marginBottom: '2px' }}>
                <span>🚗 {t.mobilityWeight || (isRu ? 'Вес мобильности (скорость, задержки)' : 'Mobility Weight (delay, speed)')}</span>
                <strong>{Math.round((customWeights?.mobility ?? 0.34) * 100)}%</strong>
              </div>
              <input
                type="range"
                min="5"
                max="90"
                value={Math.round((customWeights?.mobility ?? 0.34) * 100)}
                onChange={e => handleSliderChange('mobility', e.target.value)}
                style={{ width: '100%', accentColor: '#38bdf8' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', marginBottom: '2px' }}>
                <span>🌱 {t.ecoWeight || (isRu ? 'Вес экологии (выбросы CO₂, NOₓ)' : 'Eco Weight (emissions, idling)')}</span>
                <strong>{Math.round((customWeights?.environment ?? 0.33) * 100)}%</strong>
              </div>
              <input
                type="range"
                min="5"
                max="90"
                value={Math.round((customWeights?.environment ?? 0.33) * 100)}
                onChange={e => handleSliderChange('environment', e.target.value)}
                style={{ width: '100%', accentColor: '#4ade80' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', marginBottom: '2px' }}>
                <span>🚶 {t.accessWeight || (isRu ? 'Вес доступности (пешеходы, безопасность)' : 'Access Weight (pedestrian, safety)')}</span>
                <strong>{Math.round((customWeights?.accessibility ?? 0.33) * 100)}%</strong>
              </div>
              <input
                type="range"
                min="5"
                max="90"
                value={Math.round((customWeights?.accessibility ?? 0.33) * 100)}
                onChange={e => handleSliderChange('accessibility', e.target.value)}
                style={{ width: '100%', accentColor: '#fbbf24' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

