import { useState, useEffect } from 'react'
import {
  exportDecisionReportToJson,
  exportDecisionReportToCsv,
  exportDecisionReportToPdf
} from '../../utils/export'
import { safeNumber, formatSafeNumber } from '../../utils/normalize'

export function DecisionReportModal({
  isOpen,
  onClose,
  report,
  language = 'en',
  t = {},
}) {
  const isRu = language === 'ru'
  const [activeSubTab, setActiveSubTab] = useState('brief')
  const [isExporting, setIsExporting] = useState(false)
  const [showRubricModal, setShowRubricModal] = useState(false)

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen || !report) return null

  const exec = report.executive_summary || {}
  const audit = report.policy_audit || {}
  const metrics = report.metric_comparison || []
  const tradeoffs = report.tradeoffs || {}
  const robustness = report.robustness || {}
  const methodology = report.methodology || {}
  const limitations = report.limitations || {}
  const ai = report.ai_analysis
  const spatial = report.spatial_scope || {}
  const crossDistrict = report.cross_district_context
  const evidence = report.evidence_status || { level: 'MODERATE', score: 65, criteria_breakdown: {} }
  const calib = report.calibration_status || { status: 'UNCALIBRATED', traffic_calibrated: false }
  const mvr = report.model_vs_reality || { observed_metrics: [], simulated_metrics: [], derived_metrics: [] }
  const nextAction = report.next_action || {
    action_code: 'FIELD_DETECTOR_VALIDATION',
    title_en: 'Plan verified temporary turning-count validation',
    title_ru: 'Спланировать проверку поворотных потоков с помощью временных детекторов',
    priority: 'HIGH',
  }

  const handleExportJson = () => {
    exportDecisionReportToJson(report)
  }

  const handleExportCsv = async () => {
    setIsExporting(true)
    try {
      await exportDecisionReportToCsv(report)
    } finally {
      setIsExporting(false)
    }
  }

  const handleExportPdf = async () => {
    setIsExporting(true)
    try {
      await exportDecisionReportToPdf(report, language)
    } finally {
      setIsExporting(false)
    }
  }

  const renderDeltaBadge = (row) => {
    const pct = safeNumber(row.percentage_change, 0)
    const isImp = row.is_improvement
    const isNeutral = Math.abs(pct) < 0.05

    if (isNeutral) {
      return <span className="comparison-imp-badge imp-neutral">0.0%</span>
    }

    const sign = pct > 0 ? '+' : ''
    const arrow = row.direction === 'minimize' ? (isImp ? '↓' : '↑') : (isImp ? '↑' : '↓')
    const colorClass = isImp ? 'imp-positive' : 'imp-negative'

    return (
      <span className={`comparison-imp-badge ${colorClass}`}>
        {arrow} {sign}{pct.toFixed(1)}%
      </span>
    )
  }

  const getProvenanceBadgeClass = (prov) => {
    const p = (prov || '').toLowerCase()
    if (p.includes('direct')) return 'direct'
    if (p.includes('simul')) return 'simulated'
    if (p.includes('observ')) return 'observed'
    if (p.includes('estim')) return 'estimated'
    return 'ai'
  }

  const getEvidenceColor = (lvl) => {
    if (lvl === 'HIGH') return '#4ade80'
    if (lvl === 'MODERATE') return '#fbbf24'
    return '#f87171'
  }

  return (
    <div
      className="modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 10, 20, 0.88)',
        backdropFilter: 'blur(14px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
    >
      <div
        className="decision-report-workspace panel-card"
        style={{
          width: '100%',
          maxWidth: '1140px',
          maxHeight: '94vh',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: 'var(--bg-base, #0b1329)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          borderRadius: '16px',
          boxShadow: '0 25px 60px -15px rgba(0, 0, 0, 0.7), 0 0 40px rgba(56, 189, 248, 0.15)',
          overflow: 'hidden',
          animation: 'fade-in 0.25s ease-out',
        }}
      >
        {/* Header Bar */}
        <div
          style={{
            padding: '1.1rem 1.5rem',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(15, 23, 42, 0.75) 100%)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '1rem',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
              <span className="brand-mark" style={{ width: '26px', height: '26px', fontSize: '0.85rem' }}>U</span>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em', color: '#38bdf8', textTransform: 'uppercase' }}>
                URBANMIND {t.decisionReport || (isRu ? 'ОТЧЕТ О ПРИНЯТИИ РЕШЕНИЯ' : 'DECISION REPORT')}
              </span>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {report.report_id}
              </span>
            </div>
            {/* Spatial Context Breadcrumb */}
            <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span>📍</span>
              <span>{spatial.city_name || 'Tashkent'}</span>
              <span style={{ color: 'var(--text-muted)' }}>›</span>
              <span>{isRu ? (spatial.district_name_ru || spatial.district_name || 'Неверифицированный демонстрационный район') : (spatial.district_name || 'Unverified demonstration district')}</span>
              <span style={{ color: 'var(--text-muted)' }}>›</span>
              <span style={{ color: '#38bdf8' }}>{isRu ? (spatial.corridor_name_ru || spatial.corridor_name || 'Центральный коридор') : (spatial.corridor_name || 'Central Corridor')}</span>
            </div>
          </div>

          {/* Action Toolbar */}
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button
              type="button"
              className="ghost-button"
              onClick={handleExportJson}
              style={{ fontSize: '0.8rem', padding: '0.45rem 0.8rem' }}
              title="Download full decision report JSON"
            >
              📥 JSON
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={handleExportCsv}
              disabled={isExporting}
              style={{ fontSize: '0.8rem', padding: '0.45rem 0.8rem' }}
              title="Download metrics and audit CSV"
            >
              📊 CSV
            </button>
            <button
              type="button"
              className="accent"
              onClick={handleExportPdf}
              disabled={isExporting}
              style={{ fontSize: '0.8rem', padding: '0.45rem 0.95rem' }}
              title="Open printable stakeholder PDF view"
            >
              📄 {t.printReport || (isRu ? 'Печать / PDF' : 'Print / PDF')}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={onClose}
              style={{ fontSize: '1.1rem', padding: '0.3rem 0.6rem', marginLeft: '0.25rem', color: 'var(--text-muted)' }}
              title="Close report"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Workspace Navigation Subtabs */}
        <div
          style={{
            display: 'flex',
            gap: '0.4rem',
            padding: '0.6rem 1.5rem 0',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            background: 'rgba(15, 23, 42, 0.4)',
            overflowX: 'auto',
          }}
        >
          {[
            { id: 'brief', label: isRu ? '⚡ Краткое резюме для руководства' : '⚡ Decision Brief' },
            { id: 'model_vs_reality', label: isRu ? '🔍 Модель и реальность' : '🔍 Model vs Reality' },
            { id: 'policy', label: isRu ? '🎯 Аудит политики' : '🎯 Policy & Objectives' },
            { id: 'metrics', label: isRu ? '📊 Сравнение метрик' : '📊 Metric Comparison' },
            { id: 'tradeoffs', label: isRu ? '⚖️ Компромиссы' : '⚖️ Trade-offs' },
            { id: 'robustness', label: isRu ? '📈 Устойчивость' : '📈 Robustness' },
            { id: 'methodology', label: isRu ? '🔬 Методология и Ограничения' : '🔬 Methodology & Limitations' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveSubTab(tab.id)}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: activeSubTab === tab.id ? '2px solid #38bdf8' : '2px solid transparent',
                borderRadius: 0,
                color: activeSubTab === tab.id ? '#38bdf8' : 'var(--text-muted)',
                padding: '0.5rem 0.85rem',
                fontWeight: activeSubTab === tab.id ? 700 : 500,
                cursor: 'pointer',
                fontSize: '0.84rem',
                marginBottom: '-1px',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div
          style={{
            padding: '1.4rem 1.5rem',
            overflowY: 'auto',
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem',
          }}
        >
          {/* TAB 1: 15-SECOND DECISION BRIEF */}
          {activeSubTab === 'brief' && (
            <>
              {/* Top Decision Brief Card */}
              <div
                style={{
                  background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%)',
                  border: '2px solid rgba(56, 189, 248, 0.4)',
                  borderRadius: '12px',
                  padding: '1.35rem',
                  boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.9rem', flexWrap: 'wrap', gap: '0.6rem' }}>
                  <div>
                    <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                      {isRu ? '15-СЕКУНДНОЕ РЕЗЮМЕ ДЛЯ РУКОВОДСТВА' : '15-SECOND MUNICIPAL DECISION BRIEF'}
                    </span>
                    <h3 style={{ margin: '3px 0 0 0', fontSize: '1.2rem', color: '#ffffff', fontWeight: 800 }}>
                      {isRu ? 'Рекомендуемый кандидат для полевой валидации' : 'Simulation-Supported Candidate for Field Validation'}
                    </h3>
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    {/* Evidence Strength Badge with Rubric Trigger */}
                    <button
                      type="button"
                      onClick={() => setShowRubricModal(!showRubricModal)}
                      style={{
                        background: `rgba(${evidence.level === 'HIGH' ? '74, 222, 128' : (evidence.level === 'MODERATE' ? '251, 191, 36' : '248, 113, 113')}, 0.15)`,
                        border: `1px solid ${getEvidenceColor(evidence.level)}`,
                        color: getEvidenceColor(evidence.level),
                        borderRadius: '6px',
                        padding: '0.35rem 0.65rem',
                        fontSize: '0.78rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                      title="Click to view transparent evidence strength rubric"
                    >
                      <span>🛡️ {isRu ? 'Сила доказательств:' : 'Evidence:'} {evidence.level} ({evidence.score}/100)</span>
                    </button>

                    {/* Calibration Status Badge */}
                    <span
                      style={{
                        background: 'rgba(217, 119, 6, 0.15)',
                        border: '1px solid #d97706',
                        color: '#fbbf24',
                        borderRadius: '6px',
                        padding: '0.35rem 0.65rem',
                        fontSize: '0.78rem',
                        fontWeight: 700,
                      }}
                    >
                      ⚙️ {calib.status}
                    </span>
                  </div>
                </div>

                {/* Candidate highlight */}
                <div style={{ background: 'rgba(56, 189, 248, 0.08)', padding: '0.85rem 1rem', borderRadius: '8px', borderLeft: '4px solid #38bdf8', marginBottom: '1.1rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>
                    {isRu ? 'Вариант мер' : 'Candidate Intervention'}
                  </span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>
                    {isRu ? (exec.recommended_intervention_ru || exec.recommended_intervention) : exec.recommended_intervention}
                  </div>
                </div>

                {/* 3-Box KPI Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.85rem', marginBottom: '1.1rem' }}>
                  <div style={{ background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.2)', borderRadius: '8px', padding: '0.85rem' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                      {isRu ? 'Эффект по задержкам' : 'Delay Impact'}
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#38bdf8', marginTop: '3px' }}>
                      {isRu ? exec.primary_result_ru : exec.primary_result}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(74, 222, 128, 0.08)', border: '1px solid rgba(74, 222, 128, 0.2)', borderRadius: '8px', padding: '0.85rem' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                      {isRu ? 'Экологический эффект' : 'Environmental Impact'}
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#4ade80', marginTop: '3px' }}>
                      {isRu ? exec.environmental_result_ru : exec.environmental_result}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(251, 191, 36, 0.08)', border: '1px solid rgba(251, 191, 36, 0.2)', borderRadius: '8px', padding: '0.85rem' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                      {isRu ? 'Оценка политики' : 'Policy Score'}
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fbbf24', marginTop: '3px' }}>
                      +{audit.policy_score}% ({audit.policy_name_ru && isRu ? audit.policy_name_ru : (audit.policy_name || 'BALANCED')})
                    </div>
                  </div>
                </div>

                {/* Trade-off line */}
                <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem 0.9rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.08)', marginBottom: '1rem' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase' }}>
                    {isRu ? '⚖️ Ключевой компромисс: ' : '⚖️ Main Trade-off: '}
                  </span>
                  <span style={{ fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
                    {isRu ? exec.main_tradeoff_ru : exec.main_tradeoff}
                  </span>
                </div>

                {/* Recommended Next Action Card */}
                <div
                  style={{
                    background: 'rgba(56, 189, 248, 0.08)',
                    border: '1px solid rgba(56, 189, 248, 0.3)',
                    borderLeft: '4px solid #38bdf8',
                    borderRadius: '8px',
                    padding: '0.95rem 1.1rem',
                    marginBottom: '1rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <strong style={{ fontSize: '0.82rem', color: '#38bdf8', textTransform: 'uppercase' }}>
                      🎯 {isRu ? 'Рекомендуемое следующее действие (Полевая валидация):' : 'Recommended Next Action (Field Validation):'}
                    </strong>
                    <span style={{ fontSize: '0.72rem', background: '#38bdf8', color: '#0f172a', fontWeight: 800, padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                      {nextAction.priority || 'HIGH'} PRIORITY
                    </span>
                  </div>
                  <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#ffffff', marginBottom: '3px' }}>
                    {isRu ? nextAction.title_ru : nextAction.title_en}
                  </div>
                  <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                    {isRu ? nextAction.rationale_ru : nextAction.rationale_en}
                  </p>
                </div>

                {/* Municipal Authority Disclaimer Box */}
                <div
                  style={{
                    background: 'rgba(251, 191, 36, 0.05)',
                    border: '1px solid rgba(251, 191, 36, 0.2)',
                    borderRadius: '6px',
                    padding: '0.65rem 0.85rem',
                    fontSize: '0.78rem',
                    color: '#e2e8f0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <span style={{ fontSize: '1rem' }}>⚖️</span>
                  <span>
                    <strong>{isRu ? 'Правовая оговорка:' : 'Municipal Authority Disclaimer:'}</strong>{' '}
                    {isRu ? report.municipal_disclaimer_ru : report.municipal_disclaimer_en}
                  </span>
                </div>
              </div>

              {/* Rubric Breakdown Details (Expandable) */}
              {showRubricModal && (
                <div
                  style={{
                    background: 'rgba(15, 23, 42, 0.85)',
                    border: '1px solid rgba(56, 189, 248, 0.3)',
                    borderRadius: '12px',
                    padding: '1.2rem',
                    animation: 'fade-in 0.2s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                    <h4 style={{ margin: 0, fontSize: '0.95rem', color: '#38bdf8', fontWeight: 700 }}>
                      🛡️ {isRu ? 'Прозрачная модель оценки силы доказательств' : 'Transparent Evidence Strength Rubric'}
                    </h4>
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => setShowRubricModal(false)}
                      style={{ fontSize: '0.78rem', padding: '0.2rem 0.5rem' }}
                    >
                      ✕
                    </button>
                  </div>
                  <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    {isRu ? evidence.explanation_ru : evidence.explanation_en}
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.6rem', fontSize: '0.8rem' }}>
                    {Object.entries(evidence.criteria_breakdown || {}).map(([cKey, cVal]) => (
                      <div key={cKey} style={{ background: 'rgba(255,255,255,0.03)', padding: '0.6rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, color: '#fff', marginBottom: '2px' }}>
                          <span>{cKey.replace('_', ' ').toUpperCase()}</span>
                          <span style={{ color: cVal.status === 'PASS' ? '#4ade80' : '#fbbf24' }}>+{cVal.points} pts</span>
                        </div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{cVal.desc}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Strategic Context */}
              {ai && (
                <div
                  style={{
                    background: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(168, 85, 247, 0.3)',
                    borderRadius: '12px',
                    padding: '1.2rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                    <h4 style={{ margin: 0, fontSize: '0.95rem', color: '#e9d5ff', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      🤖 {isRu ? 'Аналитическая интерпретация ИИ' : 'Strategic AI Interpretation'}
                    </h4>
                    <span className="provenance-badge ai">
                      {ai.provenance || (ai.is_ai ? 'GEMINI 2.5' : 'RULE-BASED SUMMARY')}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', lineHeight: 1.5 }}>
                    {ai.summary}
                  </p>
                  {Array.isArray(ai.key_improvements) && ai.key_improvements.length > 0 && (
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <strong style={{ color: '#c084fc', fontSize: '0.76rem', textTransform: 'uppercase' }}>
                        {isRu ? 'Ключевые преимущества:' : 'Key Operational Advantages:'}
                      </strong>
                      {ai.key_improvements.map((imp, idx) => (
                        <div key={idx} style={{ paddingLeft: '0.5rem' }}>• {imp}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* TAB 2: MODEL VS REALITY */}
          {activeSubTab === 'model_vs_reality' && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.25rem',
              }}
            >
              <div>
                <h4 style={{ margin: 0, fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
                  🔍 {isRu ? 'Классификация данных: модель и реальность' : 'Model vs Reality Data Classification'}
                </h4>
                <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                  {isRu ? mvr.traffic_calibration_summary_ru : mvr.traffic_calibration_summary_en}
                </p>
              </div>

              {/* Observed Data Section */}
              <div>
                <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#818cf8', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span className="provenance-badge observed">OBSERVED</span> {isRu ? 'Натурные измерения (Физические датчики)' : 'Observed Field Telemetry'}
                </h5>
                <table className="comparison-table" style={{ width: '100%', fontSize: '0.82rem' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Параметр' : 'Parameter'}</th>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Значение' : 'Value'}</th>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Источник' : 'Source'}</th>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Статус' : 'State'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mvr.observed_metrics?.map((item) => (
                      <tr key={item.key}>
                        <td style={{ fontWeight: 600 }}>{isRu ? item.name_ru : item.name_en}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: item.value === 'Calibration data unavailable' ? '#fbbf24' : '#4ade80' }}>
                          {item.value} {item.unit}
                        </td>
                        <td style={{ color: 'var(--text-muted)' }}>{isRu ? item.source_ru : item.source}</td>
                        <td>
                          <span style={{ fontSize: '0.72rem', background: 'rgba(255,255,255,0.05)', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                            {item.calibration_state}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Simulated Physics Section */}
              <div>
                <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#4ade80', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span className="provenance-badge simulated">SIMULATED</span> {isRu ? 'Микроскопическая модель SUMO/TraCI' : 'Microscopic SUMO/TraCI model'}
                </h5>
                <table className="comparison-table" style={{ width: '100%', fontSize: '0.82rem' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Параметр' : 'Parameter'}</th>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Значение' : 'Value'}</th>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Источник' : 'Source'}</th>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Методология' : 'Methodology'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mvr.simulated_metrics?.map((item) => (
                      <tr key={item.key}>
                        <td style={{ fontWeight: 600 }}>{isRu ? item.name_ru : item.name_en}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                          {item.value} {item.unit}
                        </td>
                        <td style={{ color: 'var(--text-muted)' }}>{item.source}</td>
                        <td style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>{isRu ? item.description_ru : item.description_en}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Derived Indicators Section */}
              <div>
                <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span className="provenance-badge estimated">DERIVED</span> {isRu ? 'Производные индикаторы (Движок решений)' : 'Derived Decision Indicators'}
                </h5>
                <table className="comparison-table" style={{ width: '100%', fontSize: '0.82rem' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Индикатор' : 'Indicator'}</th>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Оценка' : 'Score'}</th>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Формула / Описание' : 'Description'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mvr.derived_metrics?.map((item) => (
                      <tr key={item.key}>
                        <td style={{ fontWeight: 600 }}>{isRu ? item.name_ru : item.name_en}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#fbbf24' }}>
                          {item.value}
                        </td>
                        <td style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>{isRu ? item.description_ru : item.description_en}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: POLICY & AUDIT */}
          {activeSubTab === 'policy' && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.2rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
                    {isRu ? 'Аудит политики и весов критериев' : 'Policy Audit & Objective Weights'}
                  </h4>
                  <p style={{ margin: '3px 0 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    {isRu ? 'Многокритериальная оценка соответствия целям городского развития' : 'Multi-objective alignment score and constraint verification'}
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block' }}>
                    {isRu ? 'Ограничения' : 'Constraints'}
                  </span>
                  <span
                    style={{
                      fontSize: '0.85rem',
                      fontWeight: 800,
                      color: audit.constraint_status === 'PASS' ? '#4ade80' : '#f87171',
                    }}
                  >
                    {audit.constraint_status === 'PASS' ? '✓ PASS' : '⚠ VIOLATION'}
                  </span>
                </div>
              </div>

              {/* Weights Breakdown Bars */}
              <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <h5 style={{ margin: '0 0 0.75rem 0', fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  {isRu ? 'Муниципальные приоритеты (Веса целей)' : 'Configured Objective Weights'}
                </h5>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                  {Object.entries(audit.policy_weights || {}).map(([key, val]) => {
                    const label = key === 'mobility' ? (isRu ? 'Мобильность' : 'Mobility') : (key === 'environment' ? (isRu ? 'Экология' : 'Environment') : (isRu ? 'Доступность' : 'Accessibility'))
                    const score = key === 'mobility' ? audit.mobility_score : (key === 'environment' ? audit.environment_score : audit.accessibility_score)
                    const color = key === 'mobility' ? '#38bdf8' : (key === 'environment' ? '#4ade80' : '#fbbf24')
                    return (
                      <div key={key} style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                          <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
                          <strong style={{ color: '#fff' }}>{Math.round(val * 100)}%</strong>
                        </div>
                        <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden', marginBottom: '6px' }}>
                          <div style={{ width: `${Math.min(100, Math.max(0, val * 100))}%`, height: '100%', background: color }} />
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                          <span>{isRu ? 'Вклад:' : 'Contribution:'}</span>
                          <span style={{ color: score >= 0 ? '#4ade80' : '#f87171', fontWeight: 600 }}>{score > 0 ? '+' : ''}{score}%</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Why This Won Rationale Card */}
              {(report.why_won || audit.why_won) && (
                <div style={{ background: 'rgba(56, 189, 248, 0.08)', padding: '0.9rem', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', marginBottom: '4px' }}>
                    🏆 {isRu ? 'Обоснование выбора победителя' : 'Deterministic Winner Selection Rationale'}
                  </div>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.45 }}>
                    {isRu ? (report.why_won_ru || report.why_won || audit.why_won_ru || audit.why_won) : (report.why_won_en || report.why_won || audit.why_won_en || audit.why_won)}
                  </p>
                </div>
              )}

              {/* Cross-Policy Outcome Comparison */}
              {report.policy_comparison && Object.keys(report.policy_comparison).length > 0 && (
                <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <h5 style={{ margin: 0, fontSize: '0.82rem', color: '#fff', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      ⚖️ {isRu ? 'Сравнение результатов по политикам (ПОТОК, ЭКО, БАЛАНС)' : 'Cross-Policy Outcome Comparison'}
                    </h5>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {isRu ? 'Единая симуляционная база' : 'Single Evidence Set'}
                    </span>
                  </div>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="comparison-table" style={{ width: '100%', fontSize: '0.8rem' }}>
                      <thead>
                        <tr>
                          <th style={{ textAlign: 'left' }}>{isRu ? 'Политика' : 'Policy'}</th>
                          <th style={{ textAlign: 'left' }}>{isRu ? 'Победитель' : 'Winner'}</th>
                          <th style={{ textAlign: 'center' }}>{isRu ? 'Оценка' : 'Score'}</th>
                          <th style={{ textAlign: 'center' }}>{isRu ? 'Задержка' : 'Delay'}</th>
                          <th style={{ textAlign: 'center' }}>CO₂</th>
                          <th style={{ textAlign: 'center' }}>{isRu ? 'Поток' : 'Throughput'}</th>
                          <th style={{ textAlign: 'left' }}>{isRu ? 'Обоснование' : 'Rationale'}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(report.policy_comparison).map(([pKey, pVal]) => {
                          if (!pVal || typeof pVal !== 'object') return null
                          const isCur = report.policy_id === pVal.policy_id || report.active_policy === pVal.policy_id
                          const pScore = Number(pVal.overall_score || 0)
                          return (
                            <tr key={pKey} style={{ background: isCur ? 'rgba(56, 189, 248, 0.1)' : 'transparent' }}>
                              <td style={{ fontWeight: 700, color: isCur ? '#38bdf8' : '#fff' }}>
                                {pVal.icon || '🎯'} {isRu ? (pVal.policy_name_ru || pVal.policy_name) : pVal.policy_name}
                              </td>
                              <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                                {pVal.best_candidate_label || pVal.best_candidate_id}
                              </td>
                              <td style={{ textAlign: 'center', fontWeight: 700, color: pScore >= 0 ? '#4ade80' : '#f87171' }}>
                                {pScore > 0 ? '+' : ''}{pScore.toFixed(1)}%
                              </td>
                              <td style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                                {Number(pVal.average_waiting_seconds || 0).toFixed(1)}s
                              </td>
                              <td style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                                {Number(pVal.sumo_co2_kg || 0).toFixed(4)}kg
                              </td>
                              <td style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                                {Number(pVal.throughput_vehicles_per_hour || 0).toFixed(0)}
                              </td>
                              <td style={{ fontSize: '0.72rem', color: 'var(--text-muted)', maxWidth: '240px' }}>
                                {isRu ? (pVal.why_won_ru || pVal.why_won) : (pVal.why_won_en || pVal.why_won)}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Cross-District Context Pill */}
              {crossDistrict && (
                <div style={{ background: 'rgba(56, 189, 248, 0.05)', padding: '0.9rem', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', marginBottom: '4px' }}>
                    🌐 {isRu ? 'Межрайонная пространственная готовность' : 'Cross-District Spatial Scope Readiness'}
                  </div>
                  <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    {isRu
                      ? 'Межрайонные связи не верифицированы в текущем демонстрационном наборе. Внешние эффекты очередей не оценены.'
                      : 'Cross-district relationships are not verified in the current demonstration dataset; spillover effects have not been evaluated.'}
                  </p>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', fontSize: '0.74rem' }}>
                    <span style={{ padding: '0.2rem 0.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', color: '#cbd5e1' }}>
                      {isRu ? 'Риск перелива очередей: НЕ ОЦЕНЕН' : 'Spillover Queue Risk: NOT EVALUATED'}
                    </span>
                    <span style={{ padding: '0.2rem 0.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', color: '#cbd5e1' }}>
                      {isRu ? 'Транзитная связность: НЕ ОЦЕНЕНА' : 'Transit Continuity: NOT EVALUATED'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}


          {/* TAB 4: METRIC COMPARISON */}
          {activeSubTab === 'metrics' && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '1.25rem',
              }}
            >
              <h4 style={{ margin: '0 0 0.85rem 0', fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
                {isRu ? 'Сравнение метрик: базовый и оптимизированный коридор' : 'Corridor Metrics: Baseline vs. Optimized'}
              </h4>
              <div style={{ overflowX: 'auto' }}>
                <table className="comparison-table" style={{ width: '100%', fontSize: '0.84rem' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Метрика' : 'Metric'}</th>
                      <th style={{ textAlign: 'right' }}>{isRu ? 'Базовый' : 'Baseline'}</th>
                      <th style={{ textAlign: 'right' }}>{isRu ? 'Оптимизировано' : 'Optimized'}</th>
                      <th style={{ textAlign: 'right' }}>{isRu ? 'Абс. изм.' : 'Abs Change'}</th>
                      <th style={{ textAlign: 'right' }}>{isRu ? 'Эффект (Δ)' : 'Effect (Δ)'}</th>
                      <th style={{ textAlign: 'center' }}>{isRu ? 'Происхождение' : 'Provenance'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.map((row) => (
                      <tr key={row.key}>
                        <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                          {isRu ? row.name_ru : row.name_en}
                        </td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                          {formatSafeNumber(row.baseline, 1)} {row.unit}
                        </td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#fff' }}>
                          {formatSafeNumber(row.optimized, 1)} {row.unit}
                        </td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                          {row.absolute_change > 0 ? '+' : ''}{row.absolute_change} {row.unit}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          {renderDeltaBadge(row)}
                        </td>
                        <td style={{ textAlign: 'center' }}>
                          <span className={`provenance-badge ${getProvenanceBadgeClass(row.provenance)}`}>
                            {row.provenance}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: TRADEOFFS */}
          {activeSubTab === 'tradeoffs' && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div>
                <h4 style={{ margin: 0, fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
                  {isRu ? 'Многокритериальный анализ компромиссов' : 'Multi-Objective Trade-off Analysis'}
                </h4>
                <p style={{ margin: '4px 0 0 0', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                  {isRu ? (tradeoffs.verdict_ru || tradeoffs.verdict_en) : (tradeoffs.verdict_en || tradeoffs.verdict_ru)}
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                {/* Improved */}
                <div style={{ background: 'rgba(34, 197, 94, 0.08)', border: '1px solid rgba(34, 197, 94, 0.25)', borderRadius: '8px', padding: '1rem' }}>
                  <strong style={{ color: '#4ade80', fontSize: '0.85rem', display: 'block', marginBottom: '0.5rem' }}>
                    🟢 {isRu ? 'Улучшено (Снижение потерь и задержек):' : 'Improved (Loss & Delay Reductions):'}
                  </strong>
                  <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.82rem', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {tradeoffs.improved?.length > 0 ? (
                      tradeoffs.improved.map((item, i) => (
                        <li key={i}>
                          <strong>{isRu ? (item.name_ru || item.name) : (item.name_en || item.name)}</strong>:{' '}
                          <span style={{ color: '#4ade80' }}>{item.change_pct || item.value}%</span>
                        </li>
                      ))
                    ) : (
                      <li>{isRu ? 'Нет значимых улучшений' : 'No major improvements'}</li>
                    )}
                  </ul>
                </div>

                {/* Worsened */}
                <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '8px', padding: '1rem' }}>
                  <strong style={{ color: '#f87171', fontSize: '0.85rem', display: 'block', marginBottom: '0.5rem' }}>
                    🟡 {isRu ? 'Компромиссы (Второстепенная нагрузка):' : 'Trade-offs (Secondary Approach Loads):'}
                  </strong>
                  <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.82rem', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {tradeoffs.worsened?.length > 0 ? (
                      tradeoffs.worsened.map((item, i) => (
                        <li key={i}>
                          <strong>{isRu ? (item.name_ru || item.name) : (item.name_en || item.name)}</strong>:{' '}
                          <span style={{ color: '#f87171' }}>+{Math.abs(item.change_pct || item.value)}%</span>
                        </li>
                      ))
                    ) : (
                      <li>{isRu ? 'Значимых негативных компромиссов не выявлено' : 'No major negative trade-offs detected'}</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: ROBUSTNESS */}
          {activeSubTab === 'robustness' && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div>
                <h4 style={{ margin: 0, fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
                  {isRu ? 'Статистическая устойчивость симуляции' : 'Simulation Statistical Evidence & Robustness'}
                </h4>
                <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  {isRu ? robustness.methodology_note_ru : robustness.methodology_note_en}
                </p>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                <span className="provenance-badge simulated">
                  {isRu ? `Выборка: ${robustness.sample_count ?? 0} прогонов` : `Sample Size: ${robustness.sample_count ?? 0} seeds`}
                </span>
                <span className="provenance-badge simulated">
                  {isRu ? '95% доверительный интервал Стьюдента по сидам моделирования' : '95% Student-t interval across simulation seeds'}
                </span>
                <span className="provenance-badge ai">
                  {isRu ? 'Детерминированное ранжирование политик' : 'Deterministic policy ranking'}
                </span>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table className="comparison-table" style={{ width: '100%', fontSize: '0.82rem' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>{isRu ? 'Метрика' : 'Metric'}</th>
                      <th style={{ textAlign: 'right' }}>Mean</th>
                      <th style={{ textAlign: 'right' }}>Std Dev (σ)</th>
                      <th style={{ textAlign: 'center' }}>95% CI</th>
                      <th style={{ textAlign: 'right' }}>Min / Max</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(robustness.stats || {}).map(([key, stat]) => {
                      const mObj = metrics.find((m) => m.key === key)
                      const name = isRu ? (mObj?.name_ru || key) : (mObj?.name_en || key)
                      return (
                        <tr key={key}>
                          <td style={{ fontWeight: 600 }}>{name}</td>
                          <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{stat.mean}</td>
                          <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>±{stat.std_dev}</td>
                          <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>[{stat.ci_95_low}, {stat.ci_95_high}]</td>
                          <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{stat.min} / {stat.max}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 7: METHODOLOGY & LIMITATIONS */}
          {activeSubTab === 'methodology' && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '1.25rem',
              }}
            >
              {/* Methodology Card */}
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  padding: '1.2rem',
                }}
              >
                <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', color: '#fff', fontWeight: 700 }}>
                  🔬 {isRu ? 'Техническая методология' : 'Technical Methodology'}
                </h4>
                <div style={{ fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', color: 'var(--text-secondary)' }}>
                  <div>
                    <strong style={{ color: '#cbd5e1' }}>{isRu ? 'Сеть:' : 'Network:'}</strong> {methodology.network_name}
                  </div>
                  <div>
                    <strong style={{ color: '#cbd5e1' }}>{isRu ? 'Движок симуляции:' : 'Simulation Engine:'}</strong> {methodology.simulation_engine}
                  </div>
                  <div>
                    <strong style={{ color: '#cbd5e1' }}>{isRu ? 'Модель выбросов:' : 'Emission Model:'}</strong> {methodology.emission_model}
                  </div>
                  <div>
                    <strong style={{ color: '#cbd5e1' }}>{isRu ? 'Шаги симуляции:' : 'Duration & Warmup:'}</strong> {methodology.duration_steps} steps ({methodology.warmup_steps} warmup)
                  </div>
                  <div>
                    <strong style={{ color: '#cbd5e1' }}>{isRu ? 'Метод оптимизации:' : 'Optimization Method:'}</strong> {methodology.optimization_method}
                  </div>
                </div>
              </div>

              {/* Limitations Card */}
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  padding: '1.2rem',
                }}
              >
                <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', color: '#fff', fontWeight: 700 }}>
                  ⚠️ {isRu ? 'Ограничения и допущения' : 'Limitations & Assumptions'}
                </h4>
                <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.6rem', color: 'var(--text-secondary)' }}>
                  <div>
                    <strong style={{ color: '#38bdf8' }}>{isRu ? 'Моделируемые данные (MODELED):' : 'Modeled Data Caveats:'}</strong>
                    <ul style={{ margin: '3px 0 0 0', paddingLeft: '1.1rem' }}>
                      {(isRu ? limitations.modeled_caveats_ru : limitations.modeled_caveats_en)?.map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <strong style={{ color: '#818cf8' }}>{isRu ? 'Натурные датчики (OBSERVED):' : 'Physical Sensor Caveats:'}</strong>
                    <ul style={{ margin: '3px 0 0 0', paddingLeft: '1.1rem' }}>
                      {(isRu ? limitations.observed_data_caveats_ru : limitations.observed_data_caveats_en)?.map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
