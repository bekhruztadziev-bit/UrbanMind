export function PolicyComparisonCard({
  t = {},
  language = 'en',
  policyComparison = null,
  activePolicy = 'balanced',
  onSelectPolicy,
}) {
  const isRu = language === 'ru'
  if (!policyComparison || typeof policyComparison !== 'object' || Object.keys(policyComparison).length === 0) {
    return null
  }

  const items = [
    policyComparison.flow,
    policyComparison.eco,
    policyComparison.balanced,
    policyComparison.custom,
  ].filter(Boolean)

  if (items.length === 0) return null

  return (
    <div className="panel-card policy-comparison-panel" style={{ padding: '1.1rem', marginTop: '1rem', border: '1.5px solid rgba(56, 189, 248, 0.25)', background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.7) 0%, rgba(30, 41, 59, 0.5) 100%)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--accent-primary)', fontWeight: 700 }}>
            {isRu ? 'ОДИН СЦЕНАРИЙ — РАЗНЫЕ ПРИОРИТЕТЫ' : 'SAME EVIDENCE · DIVERGENT POLICY OBJECTIVES'}
          </span>
          <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            ⚖️ {t.policyComparisonTitle || (isRu ? 'Сравнение результатов по политикам (ПОТОК, ЭКО, БАЛАНС)' : 'Policy Outcome Comparison')}
          </h4>
        </div>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '3px 8px', borderRadius: '4px' }}>
          {isRu ? 'Единый набор симуляционных данных' : 'Single Simulation Evidence Set'}
        </span>
      </div>

      {/* Grid of Policy Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(items.length, 3)}, 1fr)`, gap: '0.75rem', marginBottom: '0.85rem' }}>
        {items.map((item) => {
          const isSelected = activePolicy === item.policy_id
          const name = isRu ? item.policy_name_ru || item.policy_name : item.policy_name
          const question = isRu ? item.objective_question_ru || item.objective_question : item.objective_question
          const whyWon = isRu ? item.why_won_ru || item.why_won_en || item.why_won : item.why_won_en || item.why_won
          const score = Number(item.overall_score || item.best_candidate_score || 0)

          return (
            <div
              key={item.policy_id}
              onClick={() => onSelectPolicy && onSelectPolicy(item.policy_id)}
              style={{
                background: isSelected ? 'rgba(56, 189, 248, 0.12)' : 'rgba(15, 23, 42, 0.5)',
                border: isSelected ? '2px solid var(--accent-primary)' : '1px solid rgba(255,255,255,0.08)',
                borderRadius: '8px',
                padding: '0.85rem',
                cursor: onSelectPolicy ? 'pointer' : 'default',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '1.2rem' }}>{item.icon}</span>
                    <strong style={{ fontSize: '0.82rem', color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)' }}>
                      {item.policy_id.toUpperCase()}
                    </strong>
                  </div>
                  <span style={{
                    fontSize: '0.82rem',
                    fontWeight: 700,
                    color: score >= 0 ? '#4ade80' : '#f87171',
                    background: score >= 0 ? 'rgba(74, 222, 128, 0.1)' : 'rgba(248, 113, 113, 0.1)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                  }}>
                    {score > 0 ? '+' : ''}{score.toFixed(1)}%
                  </span>
                </div>

                {/* Decision Question */}
                {question && (
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontStyle: 'italic', marginBottom: '0.5rem', lineHeight: 1.3 }}>
                    «{question}»
                  </div>
                )}

                {/* Winner Candidate */}
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.5rem 0.6rem', borderRadius: '6px', marginBottom: '0.5rem' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    🏆 {isRu ? 'Победитель' : 'Winning Candidate'}
                  </div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--accent-primary)', marginTop: '2px' }}>
                    {item.best_candidate_label || item.best_candidate_id}
                  </div>
                </div>

                {/* Why This Won Deterministic Explanation */}
                {whyWon && (
                  <div style={{ fontSize: '0.73rem', color: 'var(--text-secondary)', lineHeight: 1.35, marginBottom: '0.6rem', background: 'rgba(56, 189, 248, 0.04)', padding: '0.45rem', borderRadius: '4px', borderLeft: '3px solid var(--accent-primary)' }}>
                    {whyWon}
                  </div>
                )}
              </div>

              {/* Key Impact KPIs */}
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4px', textAlign: 'center', fontSize: '0.7rem', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '0.5rem' }}>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '3px', borderRadius: '4px' }}>
                    <div style={{ color: 'var(--text-muted)' }}>{isRu ? 'Задержка' : 'Delay'}</div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{Number(item.average_waiting_seconds || 0).toFixed(1)}s</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '3px', borderRadius: '4px' }}>
                    <div style={{ color: 'var(--text-muted)' }}>CO₂</div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{Number(item.sumo_co2_kg || 0).toFixed(4)}kg</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '3px', borderRadius: '4px' }}>
                    <div style={{ color: 'var(--text-muted)' }}>{isRu ? 'Поток' : 'Throughput'}</div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{Number(item.throughput_vehicles_per_hour || 0).toFixed(0)}</div>
                  </div>
                </div>

                {/* Selection state button */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    if (onSelectPolicy) onSelectPolicy(item.policy_id)
                  }}
                  style={{
                    width: '100%',
                    marginTop: '0.6rem',
                    padding: '0.35rem',
                    borderRadius: '4px',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    border: 'none',
                    background: isSelected ? 'var(--accent-primary)' : 'rgba(255,255,255,0.08)',
                    color: isSelected ? '#0f172a' : 'var(--text-primary)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {isSelected ? (isRu ? '✓ Активная политика' : '✓ Active Policy') : (isRu ? 'Выбрать эту политику' : 'Select Policy')}
                </button>
              </div>
            </div>
          )
        })}
      </div>

      <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.35 }}>
        💡 {t.policyNote || (isRu ? 'Каждая политика оценивает один и тот же массив моделирования с разными приоритетами. Детерминированные веса определяют выбор кандидата.' : 'Each policy evaluates the exact same simulation evidence with differing objective weights. Deterministic scoring guides the municipal recommendation.')}
      </p>
    </div>
  )
}
