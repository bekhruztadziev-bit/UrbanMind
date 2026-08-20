import { useState, useEffect, useRef, useCallback } from 'react'
import {
  exportCaseStudyToJson,
  exportCaseStudyToCsv,
  exportCaseStudyToPdf,
} from '../../utils/export'
import {
  fetchCanonicalCaseStudy,
  fetchCalibrationProtocol,
  fetchMovementMappings,
  fetchCalibrationTemplate,
  fetchCalibrationDatasets,
  importFieldObservations,
} from '../../api/client'
import { formatSafeNumber } from '../../utils/normalize'

export function CaseStudyModal({
  isOpen,
  onClose,
  language = 'en',
}) {
  const isRu = language === 'ru'
  const [activeTab, setActiveTab] = useState('brief')
  const [caseStudy, setCaseStudy] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [isExporting, setIsExporting] = useState(false)
  const [auditMode, setAuditMode] = useState(false)
  const [selectedProvenance, setSelectedProvenance] = useState(null)
  const [calibMessage, setCalibMessage] = useState('')
  const [importPurpose, setImportPurpose] = useState('CALIBRATION')
  const [fieldProtocol, setFieldProtocol] = useState(null)
  const [mappingInfo, setMappingInfo] = useState(null)
  const [calibrationTemplate, setCalibrationTemplate] = useState(null)
  const [importDiagnostics, setImportDiagnostics] = useState(null)
  const [calibrationDatasets, setCalibrationDatasets] = useState([])
  const fileInputRef = useRef(null)

  const loadCaseStudy = useCallback(async () => {
    setLoading(true)
    setLoadError('')
    try {
      const data = await fetchCanonicalCaseStudy(language)
      setCaseStudy(data)
    } catch (err) {
      console.error('Failed to load canonical case study:', err)
      setCaseStudy(null)
      setLoadError(isRu
        ? 'Канонический кейс временно недоступен. Повторите попытку позже.'
        : 'The canonical Case Study is temporarily unavailable. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [language])

  // Load canonical case study on open
  useEffect(() => {
    if (isOpen) {
      Promise.resolve().then(loadCaseStudy)
      fetchCalibrationProtocol().then(setFieldProtocol).catch(() => null)
      fetchMovementMappings().then(setMappingInfo).catch(() => null)
      fetchCalibrationTemplate().then(setCalibrationTemplate).catch(() => null)
      fetchCalibrationDatasets().then((data) => setCalibrationDatasets(data.datasets || [])).catch(() => null)
    }
  }, [isOpen, language, loadCaseStudy])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const downloadObservationTemplate = () => {
    const header = calibrationTemplate?.csv_header || 'dataset_id,purpose,campaign_id,simulation_campaign_id,timestamp,measurement_window_id,intersection_id,approach_id,movement,interval_minutes,vehicle_count,vehicle_class,source,quality,notes'
    const blob = new Blob([`${header}\n`], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'urbanmind_field_observation_template.csv'
    anchor.click()
    URL.revokeObjectURL(url)
  }

  const beginObservationUpload = (purpose) => {
    setImportPurpose(purpose)
    fileInputRef.current?.click()
  }

  const handleObservationFile = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setLoading(true)
    try {
      const content = await file.text()
      const isCsv = file.name.toLowerCase().endsWith('.csv')
      const payload = isCsv
        ? { format: 'csv', csv_text: content, purpose: importPurpose }
        : { ...JSON.parse(content), purpose: importPurpose }
      const result = await importFieldObservations(payload)
      setImportDiagnostics(result)
      const accepted = (result.diagnostics || []).filter((item) => item.status === 'ACCEPTED').length
      setCalibMessage(isRu
        ? `Проверено строк: ${(result.diagnostics || []).length}; принято: ${accepted}; отклонено: ${(result.diagnostics || []).length - accepted}.`
        : `Rows checked: ${(result.diagnostics || []).length}; accepted: ${accepted}; rejected: ${(result.diagnostics || []).length - accepted}.`)
      fetchCalibrationDatasets().then((data) => setCalibrationDatasets(data.datasets || [])).catch(() => null)
    } catch (error) {
      setCalibMessage(isRu ? `Импорт не выполнен: ${error.message}` : `Import failed: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleExportJson = () => {
    if (caseStudy) exportCaseStudyToJson(caseStudy)
  }

  const handleExportCsv = async () => {
    if (!caseStudy) return
    setIsExporting(true)
    try {
      await exportCaseStudyToCsv(caseStudy)
    } finally {
      setIsExporting(false)
    }
  }

  const handleExportPdf = async () => {
    if (!caseStudy) return
    setIsExporting(true)
    try {
      await exportCaseStudyToPdf(caseStudy, language)
    } finally {
      setIsExporting(false)
    }
  }

  if (!isOpen) return null

  const spatial = caseStudy?.spatial_scope || {}
  const cand = caseStudy?.selected_candidate || {}
  const results = caseStudy?.key_results || {}
  const primaryOutcomes = caseStudy?.primary_outcomes || []
  const secondaryOutcomes = caseStudy?.secondary_outcomes || []
  const policyComp = caseStudy?.policy_comparison || {}
  const calib = caseStudy?.calibration_status || {}
  const repro = caseStudy?.reproducibility_record || {}
  const epStmts = caseStudy?.epistemic_statements || []
  const provViews = caseStudy?.provenance_views || {}
  const nextAction = caseStudy?.next_action || {}

  const title = isRu ? caseStudy?.title_ru || caseStudy?.title : caseStudy?.title
  const problem = isRu ? caseStudy?.problem_statement_ru || caseStudy?.problem_statement : caseStudy?.problem_statement

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
          maxWidth: '1200px',
          maxHeight: '94vh',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: 'var(--bg-base, #0b1329)',
          border: '1.5px solid rgba(56, 189, 248, 0.35)',
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
              <span style={{ fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.08em', color: '#38bdf8', textTransform: 'uppercase' }}>
                URBANMIND {isRu ? 'КАНОНИЧЕСКИЙ КЕЙС' : 'CANONICAL CASE STUDY'}
              </span>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {caseStudy?.case_id || 'UM-CS-2026-001'}
              </span>
              {repro.simulation_configuration_hash && (
                <span style={{ fontSize: '0.68rem', background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '4px', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                  HASH: {repro.simulation_configuration_hash}
                </span>
              )}
            </div>
            {/* Spatial Context Breadcrumb */}
            <div style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span>📍</span>
              <span>{spatial.city_name || 'Tashkent'}</span>
              <span style={{ color: 'var(--text-muted)' }}>›</span>
              <span>{isRu ? (spatial.district_name_ru || spatial.district_name || 'Неверифицированный демонстрационный район') : (spatial.district_name || 'Unverified demonstration district')}</span>
              <span style={{ color: 'var(--text-muted)' }}>›</span>
              <span style={{ color: '#38bdf8' }}>{isRu ? (spatial.corridor_name_ru || spatial.corridor_name || 'Центральный коридор') : (spatial.corridor_name || 'Central Corridor')}</span>
            </div>
          </div>

          {/* Action Toolbar */}
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => setAuditMode(prev => !prev)}
              style={{
                fontSize: '0.78rem',
                padding: '0.45rem 0.8rem',
                borderRadius: '6px',
                border: `1px solid ${auditMode ? '#38bdf8' : 'rgba(255, 255, 255, 0.15)'}`,
                background: auditMode ? 'rgba(56, 189, 248, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                color: auditMode ? '#38bdf8' : 'var(--text-muted)',
                fontWeight: 700,
                cursor: 'pointer',
              }}
              title="Toggle Technical Audit Mode (Reproducibility, Config Hash, Student-t CI)"
            >
              🛡️ {isRu ? 'Аудит-режим' : 'Audit Mode'}: {auditMode ? 'ON' : 'OFF'}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={handleExportJson}
              style={{ fontSize: '0.8rem', padding: '0.45rem 0.8rem' }}
              title="Download Case Study JSON"
            >
              📥 JSON
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={handleExportCsv}
              disabled={isExporting}
              style={{ fontSize: '0.8rem', padding: '0.45rem 0.8rem' }}
              title="Download Case Study CSV"
            >
              📊 CSV
            </button>
            <button
              type="button"
              className="accent"
              onClick={handleExportPdf}
              disabled={isExporting}
              style={{ fontSize: '0.8rem', padding: '0.45rem 0.95rem' }}
              title="Open printable stakeholder PDF / HTML view"
            >
              📄 {isRu ? 'Печать / PDF' : 'Print / PDF'}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={onClose}
              style={{ fontSize: '1.1rem', padding: '0.3rem 0.6rem', marginLeft: '0.25rem', color: 'var(--text-muted)' }}
              title="Close modal"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Technical Audit Mode Bar (Visible when Audit Mode is ON) */}
        {auditMode && (
          <div
            style={{
              padding: '0.6rem 1.5rem',
              background: 'rgba(56, 189, 248, 0.08)',
              borderBottom: '1px solid rgba(56, 189, 248, 0.25)',
              display: 'flex',
              gap: '1.2rem',
              alignItems: 'center',
              flexWrap: 'wrap',
              fontSize: '0.74rem',
              fontFamily: 'var(--font-mono)',
              color: '#38bdf8',
            }}
          >
            <span><strong>EXP:</strong> {repro.experiment_id || 'UM-EXP-2026-001'}</span>
            <span><strong>NET:</strong> {repro.network_version || 'not recorded'}</span>
            <span><strong>SEEDS:</strong> [{repro.seeds?.join(', ') || 'not evaluated'}] (n={repro.sample_size ?? 0})</span>
            <span><strong>CI:</strong> {repro.confidence_interval_method || 'not evaluated'}</span>
            <span><strong>AGG:</strong> {repro.aggregation_method || 'IMPROVEMENT_OF_MEAN_METRICS'}</span>
            <span><strong>CALIB:</strong> {calib.status || 'UNCALIBRATED'}</span>
          </div>
        )}

        {/* Tab Navigation */}
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
            { id: 'brief', label: isRu ? '⚡ Краткий бриф кейса' : '⚡ Case Brief & Problem' },
            { id: 'policy', label: isRu ? '⚖️ Сравнение политик' : '⚖️ Policy Comparison' },
            { id: 'findings', label: isRu ? '📊 Показатели и 95% ДИ' : '📊 Outcomes & 95% CI' },
            { id: 'model_vs_reality', label: isRu ? '🔍 Модель и реальность' : '🔍 Model vs Reality' },
            { id: 'calibration', label: isRu ? '📥 Натурная калибровка и GEH' : '📥 Calibration & GEH' },
            { id: 'boundaries', label: isRu ? '🔬 Границы знания и шаг' : '🔬 What We Know & Protocol' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid #38bdf8' : '2px solid transparent',
                borderRadius: 0,
                color: activeTab === tab.id ? '#38bdf8' : 'var(--text-muted)',
                padding: '0.5rem 0.85rem',
                fontWeight: activeTab === tab.id ? 700 : 500,
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
          {loading && (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              ⏳ {isRu ? 'Загрузка кейса…' : 'Loading Case Study…'}
            </div>
          )}

          {!loading && loadError && (
            <div
              role="alert"
              style={{
                padding: '1.25rem',
                borderRadius: '10px',
                border: '1px solid rgba(248, 113, 113, 0.4)',
                background: 'rgba(127, 29, 29, 0.18)',
                color: '#fecaca',
                lineHeight: 1.5,
              }}
            >
              <strong>{isRu ? 'Ошибка загрузки' : 'Loading error'}</strong>
              <p style={{ margin: '0.45rem 0 0' }}>{loadError}</p>
              <button
                type="button"
                className="ghost-button"
                style={{ marginTop: '0.85rem' }}
                onClick={loadCaseStudy}
              >
                {isRu ? 'Повторить' : 'Retry'}
              </button>
            </div>
          )}

          {!loading && caseStudy && (
            <>
              {/* TAB 1: BRIEF & PROBLEM */}
              {activeTab === 'brief' && (
                <>
                  <div
                    style={{
                      background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%)',
                      border: '2px solid rgba(56, 189, 248, 0.35)',
                      borderRadius: '12px',
                      padding: '1.35rem',
                      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <div>
                        <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                          {isRu ? 'КЕЙС #001 · ЦЕНТРАЛЬНЫЙ ТАШКЕНТ' : 'CASE STUDY #001 · CENTRAL TASHKENT'}
                        </span>
                        <h3 style={{ margin: '3px 0 0 0', fontSize: '1.25rem', color: '#ffffff', fontWeight: 800 }}>
                          {title}
                        </h3>
                      </div>
                      <span style={{ fontSize: '0.75rem', padding: '4px 10px', borderRadius: '4px', background: 'rgba(248, 113, 113, 0.15)', color: '#f87171', border: '1px solid rgba(248, 113, 113, 0.3)', fontWeight: 700 }}>
                        {calib.status || 'UNCALIBRATED'}
                      </span>
                    </div>

                    {/* Problem Statement Box */}
                    <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.9rem 1.1rem', borderRadius: '8px', borderLeft: '4px solid var(--accent-primary)', marginBottom: '1.1rem' }}>
                      <strong style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                        {isRu ? 'Транспортная проблема' : 'The Urban Mobility Problem'}
                      </strong>
                      <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                        {problem}
                      </p>
                    </div>

                    {/* KPI Highlights (Clickable for Provenance View) */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '1rem' }}>
                      <div
                        onClick={() => setSelectedProvenance(selectedProvenance === 'delay' ? null : 'delay')}
                        style={{ background: 'rgba(34, 197, 94, 0.08)', border: `1px solid ${selectedProvenance === 'delay' ? '#4ade80' : 'rgba(34, 197, 94, 0.25)'}`, borderRadius: '8px', padding: '0.85rem', textAlign: 'center', cursor: 'pointer' }}
                      >
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{isRu ? 'Задержки на магистрали' : 'Delay Reduction'} ℹ️</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#4ade80', marginTop: '2px' }}>{formatSafeNumber(results.delay_reduction_pct, 1)}%</div>
                      </div>
                      <div
                        onClick={() => setSelectedProvenance(selectedProvenance === 'co2' ? null : 'co2')}
                        style={{ background: 'rgba(34, 197, 94, 0.08)', border: `1px solid ${selectedProvenance === 'co2' ? '#4ade80' : 'rgba(34, 197, 94, 0.25)'}`, borderRadius: '8px', padding: '0.85rem', textAlign: 'center', cursor: 'pointer' }}
                      >
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>CO₂ {isRu ? 'Выбросы' : 'Emissions'} ℹ️</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#4ade80', marginTop: '2px' }}>{formatSafeNumber(results.co2_reduction_pct, 1)}%</div>
                      </div>
                      <div style={{ background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: '8px', padding: '0.85rem', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{isRu ? 'Пропускная способность' : 'Throughput'}</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#38bdf8', marginTop: '2px' }}>{formatSafeNumber(results.throughput_increase_pct, 1)}%</div>
                      </div>
                      <div
                        onClick={() => setSelectedProvenance(selectedProvenance === 'stops' ? null : 'stops')}
                        style={{ background: 'rgba(56, 189, 248, 0.08)', border: `1px solid ${selectedProvenance === 'stops' ? '#38bdf8' : 'rgba(56, 189, 248, 0.25)'}`, borderRadius: '8px', padding: '0.85rem', textAlign: 'center', cursor: 'pointer' }}
                      >
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{isRu ? 'Остановок на автомобиль' : 'Stops Reduction'} ℹ️</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#38bdf8', marginTop: '2px' }}>{formatSafeNumber(results.stops_reduction_pct, 1)}%</div>
                      </div>
                    </div>

                    {/* Expandable Provenance Detail Card */}
                    {selectedProvenance && provViews[selectedProvenance] && (
                      <div
                        style={{
                          background: 'rgba(15, 23, 42, 0.95)',
                          border: '1px solid #38bdf8',
                          borderRadius: '8px',
                          padding: '0.9rem',
                          marginBottom: '1rem',
                          fontSize: '0.8rem',
                          animation: 'fade-in 0.2s ease',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                          <strong style={{ color: '#38bdf8', textTransform: 'uppercase' }}>
                            🔍 {isRu ? 'Происхождение результата:' : 'Result Provenance & Audit Trace:'} {provViews[selectedProvenance].metric_name}
                          </strong>
                          <span style={{ cursor: 'pointer', color: 'var(--text-muted)' }} onClick={() => setSelectedProvenance(null)}>✕</span>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', color: 'var(--text-secondary)' }}>
                          <div><strong>{isRu ? 'Ключевое значение:' : 'Headline:'}</strong> {provViews[selectedProvenance].headline_value}</div>
                          <div><strong>{isRu ? 'Источник:' : 'Source:'}</strong> {provViews[selectedProvenance].source}</div>
                          <div><strong>{isRu ? 'Идентификатор эксперимента:' : 'Experiment ID:'}</strong> {provViews[selectedProvenance].experiment_id}</div>
                          <div><strong>{isRu ? 'Сценарий:' : 'Scenario:'}</strong> {provViews[selectedProvenance].scenario}</div>
                          <div><strong>{isRu ? 'Сиды:' : 'Seeds:'}</strong> [{provViews[selectedProvenance].seeds?.join(', ')}]</div>
                          <div><strong>{isRu ? 'Агрегация:' : 'Aggregation:'}</strong> {provViews[selectedProvenance].aggregation_method}</div>
                          <div><strong>{isRu ? 'Статистический метод:' : 'Statistical Method:'}</strong> {provViews[selectedProvenance].statistical_method}</div>
                          <div><strong>Calibration Status:</strong> {provViews[selectedProvenance].calibration_status}</div>
                        </div>
                      </div>
                    )}

                    {/* Selected Candidate Rationale */}
                    <div style={{ background: 'rgba(56, 189, 248, 0.08)', padding: '0.9rem', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', marginBottom: '3px' }}>
                        🏆 {isRu ? 'Рекомендованная мера для полевой проверки' : 'Recommended Candidate for Field Validation'}
                      </div>
                      <strong style={{ fontSize: '0.95rem', color: '#ffffff' }}>
                        {isRu ? cand.label_ru || cand.label : cand.label}
                      </strong>
                      <p style={{ margin: '4px 0 0 0', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                        {isRu ? cand.why_won_ru || cand.why_won : cand.why_won}
                      </p>
                    </div>
                  </div>
                </>
              )}

              {/* TAB 2: POLICY COMPARISON */}
              {activeTab === 'policy' && (
                <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '12px', padding: '1.25rem' }}>
                  <div style={{ marginBottom: '1rem' }}>
                    <h4 style={{ margin: 0, fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
                      ⚖️ {isRu ? 'Сравнение результатов по политикам (ПОТОК, ЭКО, БАЛАНС)' : 'Cross-Policy Outcome Comparison'}
                    </h4>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      {isRu ? 'Каждая политика оценивает единый симуляционный массив с различными весами целей.' : 'Each policy evaluates the exact same shared simulation evidence with distinct objective priorities.'}
                    </p>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                    {Object.entries(policyComp).map(([pKey, pItem]) => {
                      if (!pItem || typeof pItem !== 'object') return null
                      const score = Number(pItem.overall_score || 0)
                      return (
                        <div key={pKey} style={{ background: 'rgba(0, 0, 0, 0.3)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '8px', padding: '1rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <strong style={{ color: '#38bdf8', fontSize: '0.9rem' }}>
                              {pItem.icon || '🎯'} {pKey.toUpperCase()}
                            </strong>
                            <span style={{ fontWeight: 700, color: score >= 0 ? '#4ade80' : '#f87171' }}>
                              {score > 0 ? '+' : ''}{score.toFixed(1)}%
                            </span>
                          </div>
                          <div style={{ fontSize: '0.84rem', fontWeight: 600, color: '#fff', marginBottom: '0.5rem' }}>
                            {pItem.best_candidate_label || pItem.best_candidate_id}
                          </div>
                          <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', lineHeight: 1.4, margin: '0 0 0.75rem 0' }}>
                            {isRu ? pItem.why_won_ru || pItem.why_won : pItem.why_won}
                          </p>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4px', textAlign: 'center', fontSize: '0.72rem', borderTop: '1px solid rgba(255, 255, 255, 0.06)', paddingTop: '0.5rem' }}>
                            <div>
                              <div style={{ color: 'var(--text-muted)' }}>{isRu ? 'Задержка' : 'Delay'}</div>
                              <div style={{ fontWeight: 600, color: '#fff' }}>{Number(pItem.average_waiting_seconds || 0).toFixed(1)}s</div>
                            </div>
                            <div>
                              <div style={{ color: 'var(--text-muted)' }}>CO₂</div>
                              <div style={{ fontWeight: 600, color: '#fff' }}>{Number(pItem.sumo_co2_kg || 0).toFixed(4)}kg</div>
                            </div>
                            <div>
                              <div style={{ color: 'var(--text-muted)' }}>{isRu ? 'Поток' : 'Throughput'}</div>
                              <div style={{ fontWeight: 600, color: '#fff' }}>{Number(pItem.throughput_vehicles_per_hour || 0).toFixed(0)}</div>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* TAB 3: PRIMARY & SECONDARY OUTCOMES & STUDENT-T CI */}
              {activeTab === 'findings' && (
                <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
                      📊 {isRu ? 'Первичные и вторичные показатели (95% ДИ Стьюдента, df=2, t=4,303)' : 'Primary & Secondary Outcomes (95% Student-t CI, df=2, t=4.303)'}
                    </h4>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      {isRu ? 'Показатели рассчитаны по каноническому протоколу многосидового микромоделирования.' : 'Metrics computed under the canonical multi-seed protocol with exact Student-t confidence intervals.'}
                    </p>
                  </div>

                  {/* Primary Outcomes Table */}
                  <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', marginBottom: '4px' }}>
                      🚗 {isRu ? 'Первичные показатели мобильности' : 'Primary Mobility Outcomes'}
                    </div>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                      <thead>
                        <tr style={{ background: 'rgba(0,0,0,0.3)', color: 'var(--text-muted)' }}>
                          <th style={{ padding: '6px 8px', textAlign: 'left' }}>{isRu ? 'Показатель' : 'Metric'}</th>
                          <th style={{ padding: '6px 8px', textAlign: 'center' }}>{isRu ? 'Базовый' : 'Baseline'}</th>
                          <th style={{ padding: '6px 8px', textAlign: 'center' }}>{isRu ? 'Оптимизированный' : 'Optimized'}</th>
                          <th style={{ padding: '6px 8px', textAlign: 'center' }}>{isRu ? 'Дельта' : 'Abs Delta'}</th>
                          <th style={{ padding: '6px 8px', textAlign: 'center' }}>{isRu ? 'Отн. %' : 'Rel %'}</th>
                          <th style={{ padding: '6px 8px', textAlign: 'center' }}>{isRu ? '95% ДИ Стьюдента' : '95% Student-t CI'}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {primaryOutcomes.map((p, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                            <td style={{ padding: '6px 8px', fontWeight: 600, color: '#fff' }}>{isRu ? p.name_ru : p.name_en}</td>
                            <td style={{ padding: '6px 8px', textAlign: 'center', color: 'var(--text-secondary)' }}>{p.baseline} {p.unit}</td>
                            <td style={{ padding: '6px 8px', textAlign: 'center', color: '#fff', fontWeight: 600 }}>{p.optimized} {p.unit}</td>
                            <td style={{ padding: '6px 8px', textAlign: 'center', color: p.is_improvement ? '#4ade80' : '#f87171' }}>{p.absolute_delta} {p.unit}</td>
                            <td style={{ padding: '6px 8px', textAlign: 'center', fontWeight: 700, color: p.is_improvement ? '#4ade80' : '#f87171' }}>{p.relative_delta_pct}%</td>
                            <td style={{ padding: '6px 8px', textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: '0.74rem', color: '#38bdf8' }}>[{p.ci_95_low}, {p.ci_95_high}] {p.unit}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Secondary Outcomes Table */}
                  <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#a855f7', textTransform: 'uppercase', marginBottom: '4px' }}>
                      🌿 {isRu ? 'Вторичные экологические и пространственные показатели' : 'Secondary Environmental & Spatial Outcomes'}
                    </div>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                      <thead>
                        <tr style={{ background: 'rgba(0,0,0,0.3)', color: 'var(--text-muted)' }}>
                          <th style={{ padding: '6px 8px', textAlign: 'left' }}>{isRu ? 'Показатель' : 'Metric'}</th>
                          <th style={{ padding: '6px 8px', textAlign: 'center' }}>{isRu ? 'Базовый' : 'Baseline'}</th>
                          <th style={{ padding: '6px 8px', textAlign: 'center' }}>{isRu ? 'Оптимизированный' : 'Optimized'}</th>
                          <th style={{ padding: '6px 8px', textAlign: 'center' }}>{isRu ? 'Дельта' : 'Abs Delta'}</th>
                          <th style={{ padding: '6px 8px', textAlign: 'center' }}>{isRu ? 'Отн. %' : 'Rel %'}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {secondaryOutcomes.map((s, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                            <td style={{ padding: '6px 8px', fontWeight: 600, color: '#fff' }}>{isRu ? s.name_ru : s.name_en}</td>
                            <td style={{ padding: '6px 8px', textAlign: 'center', color: 'var(--text-secondary)' }}>{s.baseline} {s.unit}</td>
                            <td style={{ padding: '6px 8px', textAlign: 'center', color: '#fff', fontWeight: 600 }}>{s.optimized} {s.unit}</td>
                            <td style={{ padding: '6px 8px', textAlign: 'center', color: s.is_improvement ? '#4ade80' : '#f87171' }}>{s.absolute_delta} {s.unit}</td>
                            <td style={{ padding: '6px 8px', textAlign: 'center', fontWeight: 700, color: s.is_improvement ? '#4ade80' : '#f87171' }}>{s.relative_delta_pct}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 4: MODEL VS REALITY & EPISTEMIC CLASSIFICATION */}
              {activeTab === 'model_vs_reality' && (
                <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
                      🔍 {isRu ? 'Эпистемическая классификация утверждений' : 'Epistemic Classification of Factual Statements'}
                    </h4>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      {isRu ? 'Строгое разграничение натурных наблюдений, симуляционных расчетов, допущений и формульных индексов.' : 'Strict methodological separation between observed telemetry, simulated physics, domain assumptions, and derived indices.'}
                    </p>
                  </div>

                  {/* Epistemic Statements Table */}
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                    <thead>
                      <tr style={{ background: 'rgba(0,0,0,0.3)', color: 'var(--text-muted)' }}>
                        <th style={{ padding: '6px 8px', textAlign: 'left', width: '70px' }}>ID</th>
                        <th style={{ padding: '6px 8px', textAlign: 'left', width: '110px' }}>{isRu ? 'Категория' : 'Category'}</th>
                        <th style={{ padding: '6px 8px', textAlign: 'left' }}>{isRu ? 'Утверждение' : 'Statement'}</th>
                        <th style={{ padding: '6px 8px', textAlign: 'left', width: '220px' }}>{isRu ? 'Источник / Методология' : 'Source / Methodology'}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {epStmts.map((ep, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                          <td style={{ padding: '6px 8px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{ep.statement_id}</td>
                          <td style={{ padding: '6px 8px' }}>
                            <span
                              style={{
                                display: 'inline-block',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontSize: '0.72rem',
                                fontWeight: 700,
                                background: ep.category === 'OBSERVED' ? 'rgba(74, 222, 128, 0.15)' : ep.category === 'SIMULATED' ? 'rgba(56, 189, 248, 0.15)' : ep.category === 'DERIVED' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(251, 191, 36, 0.15)',
                                color: ep.category === 'OBSERVED' ? '#4ade80' : ep.category === 'SIMULATED' ? '#38bdf8' : ep.category === 'DERIVED' ? '#c084fc' : '#fbbf24',
                              }}
                            >
                              {ep.category}
                            </span>
                          </td>
                          <td style={{ padding: '6px 8px', color: '#fff' }}>{isRu ? ep.text_ru : ep.text_en}</td>
                          <td style={{ padding: '6px 8px', color: 'var(--text-secondary)', fontSize: '0.76rem' }}>{isRu ? ep.source_ru : ep.source}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* TAB 5: FIELD CALIBRATION & GEH STANDARD */}
              {activeTab === 'calibration' && (
                <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h4 style={{ margin: 0, fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
                        📥 {isRu ? 'Импорт натурных данных, калибровка и критерий GEH' : 'Field Observation Import, Calibration & GEH Validation'}
                      </h4>
                      <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                        {isRu ? 'Калибровочный и независимый проверочный (holdout) наборы разделены. Для статуса VALIDATED применяются настроенные критерии UrbanMind, включая GEH.' : 'Calibration and independent holdout datasets are separated. VALIDATED uses UrbanMind configured acceptance criteria, including GEH.'}
                      </p>
                    </div>
                    <span style={{ fontSize: '0.78rem', padding: '4px 10px', borderRadius: '4px', background: calib.status === 'VALIDATED' ? 'rgba(74, 222, 128, 0.2)' : calib.status === 'CALIBRATED' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(248, 113, 113, 0.15)', color: calib.status === 'VALIDATED' ? '#4ade80' : calib.status === 'CALIBRATED' ? '#38bdf8' : '#f87171', fontWeight: 700 }}>
                      {calib.status || 'UNCALIBRATED'}
                    </span>
                  </div>

                  {calibMessage && (
                    <div style={{ background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '6px', padding: '0.75rem', fontSize: '0.82rem', color: '#fff' }}>
                      ℹ️ {calibMessage}
                    </div>
                  )}

                  <input ref={fileInputRef} type="file" accept=".csv,.json,application/json,text/csv" onChange={handleObservationFile} style={{ display: 'none' }} />

                  <div style={{ background: 'rgba(251, 191, 36, 0.08)', border: '1px solid rgba(251, 191, 36, 0.28)', borderRadius: '6px', padding: '0.75rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    <strong style={{ color: '#fbbf24' }}>{isRu ? 'Сопоставление SUMO:' : 'SUMO mapping coverage:'}</strong>{' '}
                    {mappingInfo?.coverage?.enabled_movement_count || 0} {isRu ? 'подтвержденных направлений.' : 'verified movements.'}{' '}
                    {mappingInfo?.coverage?.limitation || (isRu ? 'Статус сопоставления загружается.' : 'Mapping status is loading.')}
                    {mappingInfo?.coverage?.verification_status_counts && (
                      <span style={{ display: 'block', marginTop: '4px' }}>
                        {Object.entries(mappingInfo.coverage.verification_status_counts).map(([status, count]) => `${status}: ${count}`).join(' · ')}
                      </span>
                    )}
                  </div>

                  <button type="button" className="ghost-button" onClick={downloadObservationTemplate} style={{ alignSelf: 'flex-start', padding: '0.45rem 0.85rem', fontSize: '0.78rem' }}>
                    ⇩ {isRu ? 'Скачать пустой шаблон CSV' : 'Download empty CSV template'}
                  </button>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
                    {/* Calibration Dataset Action */}
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
                      <strong style={{ fontSize: '0.86rem', color: '#38bdf8', display: 'block', marginBottom: '4px' }}>
                        1. {isRu ? 'Калибровочный набор данных (Calibration)' : 'Calibration Dataset'}
                      </strong>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '0 0 0.75rem 0' }}>
                        {isRu ? 'Используется для начальной калибровки модели спроса (переход в CALIBRATED).' : 'Used for initial demand model calibration (transition to CALIBRATED).'}
                      </p>
                      <button
                        type="button"
                        className="ghost-button"
                        onClick={() => beginObservationUpload('CALIBRATION')}
                        disabled={loading}
                        style={{ padding: '0.45rem 0.85rem', fontSize: '0.78rem', width: '100%' }}
                      >
                        📥 {isRu ? 'Загрузить CSV / JSON' : 'Upload CSV / JSON'}
                      </button>
                    </div>

                    {/* Holdout Validation Dataset Action */}
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
                      <strong style={{ fontSize: '0.86rem', color: '#4ade80', display: 'block', marginBottom: '4px' }}>
                        2. {isRu ? 'Независимый проверочный набор (holdout)' : 'Independent Holdout Dataset'}
                      </strong>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '0 0 0.75rem 0' }}>
                        {isRu ? 'Независимая проверка обязательна для перехода в статус VALIDATED с оценкой GEH.' : 'Independent verification is required for VALIDATED status with GEH evaluation.'}
                      </p>
                      <button
                        type="button"
                        className="accent"
                        onClick={() => beginObservationUpload('VALIDATION_HOLDOUT')}
                        disabled={loading}
                        style={{ padding: '0.45rem 0.85rem', fontSize: '0.78rem', width: '100%' }}
                      >
                        🛡️ {isRu ? 'Загрузить набор holdout (CSV / JSON)' : 'Upload Holdout CSV / JSON'}
                      </button>
                    </div>
                  </div>

                  {importDiagnostics && (
                    <div style={{ maxHeight: '190px', overflow: 'auto', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', padding: '0.65rem', fontSize: '0.75rem' }}>
                      <strong style={{ color: '#fff' }}>{isRu ? 'Диагностика импорта' : 'Import diagnostics'}</strong>
                      {(importDiagnostics.diagnostics || []).map((item) => (
                        <div key={item.row} style={{ marginTop: '5px', color: item.status === 'ACCEPTED' ? '#4ade80' : '#f87171' }}>
                          {isRu ? 'Строка' : 'Row'} {item.row}: {item.status}{item.errors?.length ? ` — ${item.errors.join(' ')}` : ''}
                        </div>
                      ))}
                    </div>
                  )}

                  {calibrationDatasets.length > 0 && (
                    <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                      <strong style={{ color: '#fff' }}>{isRu ? 'Импортированные наборы:' : 'Imported datasets:'}</strong>{' '}
                      {calibrationDatasets.map((item) => `${item.dataset_id} (${item.purpose}, ${item.record_count} rows)`).join(' · ')}
                    </div>
                  )}

                  <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                    {isRu ? 'Оценка калибровки остается недоступной до появления подтвержденного SUMO-сопоставления и потоков того же направления и интервала.' : 'Calibration evaluation remains unavailable until a verified SUMO mapping and comparable movement counts for the same interval are available.'}
                  </div>
                </div>
              )}

              {/* TAB 6: BOUNDARIES & PROTOCOL */}
              {activeTab === 'boundaries' && (
                <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '1rem', color: '#fff', fontWeight: 700 }}>
                      🔬 {isRu ? 'Эпистемические границы и натурный протокол валидации' : 'Scientific Boundaries & Configurable Validation Protocol'}
                    </h4>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    <div style={{ background: 'rgba(34, 197, 94, 0.08)', padding: '0.9rem', borderRadius: '8px', border: '1px solid rgba(34, 197, 94, 0.25)' }}>
                      <strong style={{ color: '#4ade80', fontSize: '0.82rem', display: 'block', marginBottom: '6px' }}>
                        ✓ {isRu ? 'Что подтверждает модель:' : 'What We Know (Empirically & Structurally):'}
                      </strong>
                      <ul style={{ margin: 0, paddingLeft: '1.1rem', fontSize: '0.8rem', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                        {(isRu ? caseStudy.what_we_know_ru : caseStudy.what_we_know_en)?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    <div style={{ background: 'rgba(245, 158, 11, 0.08)', padding: '0.9rem', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.25)' }}>
                      <strong style={{ color: '#fbbf24', fontSize: '0.82rem', display: 'block', marginBottom: '6px' }}>
                        ⚠ {isRu ? 'Что предстоит подтвердить на практике:' : 'What We Do Not Yet Know (Pending Validation):'}
                      </strong>
                      <ul style={{ margin: 0, paddingLeft: '1.1rem', fontSize: '0.8rem', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                        {(isRu ? caseStudy.what_we_do_not_know_ru : caseStudy.what_we_do_not_know_en)?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Configurable Field Protocol Inspector */}
                  {fieldProtocol && (
                    <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '0.9rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', marginBottom: '3px' }}>
                        📋 {isRu ? 'Протокол натурного пилота' : 'Configurable Field Validation Protocol'}: {fieldProtocol.protocol_id}
                      </div>
                      <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        {isRu ? fieldProtocol.description_ru : fieldProtocol.description_en}
                      </p>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                        <div><strong>{isRu ? 'Длительность:' : 'Duration:'}</strong> {fieldProtocol.recommended_duration_days} {isRu ? 'дней' : 'days'}</div>
                        <div><strong>{isRu ? 'Интервал:' : 'Interval:'}</strong> {fieldProtocol.sampling_interval_min} min</div>
                        <div><strong>{isRu ? 'Узлы:' : 'Nodes:'}</strong> {fieldProtocol.intersections?.length || 0} {isRu ? 'верифицированных перекрестков' : 'verified intersections'}</div>
                      </div>
                    </div>
                  )}

                  {/* Next Step Card */}
                  <div style={{ background: 'rgba(56, 189, 248, 0.08)', padding: '0.9rem', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', marginBottom: '3px' }}>
                      🚀 {isRu ? 'Рекомендуемый следующий шаг' : 'Recommended Next Action for Municipal Transport Authority'}
                    </div>
                    <strong style={{ fontSize: '0.92rem', color: '#fff' }}>
                      {isRu ? nextAction.title_ru : nextAction.title_en}
                    </strong>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {isRu ? 'Приоритет:' : 'Priority:'} <strong>{nextAction.priority || 'HIGH'}</strong> &nbsp;|&nbsp; 
                      {isRu ? 'Статус:' : 'Status:'} <strong>FIELD_VALIDATION_CANDIDATE</strong>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
