import { useState, useEffect } from 'react'
import { fetchPilotCases, updatePilotCase } from '../../api/client'

const DEFAULT_PILOT_CASE = {

  id: 'PILOT-TASHKENT-CENTRAL-01',
  title: 'Tashkent Central Corridor: Peak Bottleneck Mitigation',
  title_ru: 'Центральный коридор Ташкента: Устранение заторов в часы пик',
  spatial_scope: {
    id: 'central_corridor',
    name: 'Tashkent Central Corridor',
    name_ru: 'Центральный коридор Ташкента',
  },
  problem_statement: 'Draft workspace for collecting field observations and evaluating a future corridor signal pilot.',
  problem_statement_ru: 'Черновое рабочее пространство для сбора натурных наблюдений и оценки будущего пилота по управлению сигналами на коридоре.',
  objective: 'Evaluate signal coordination strategies under BALANCED policy to minimize corridor delays and vehicle stops while maintaining pedestrian crossing safety.',
  objective_ru: 'Оценка стратегий координации светофоров по политике БАЛАНС для минимизации задержек и остановок при сохранении безопасности пешеходов.',
  status: 'DRAFT',
  active_policy: 'balanced',
  baseline_summary: {},
  scenarios_tested: [],
  experiments: [],
  decision_reports: [],
  recommended_option: {},
  evidence_strength: 'NOT_AVAILABLE',
  calibration_status: 'UNCALIBRATED',
  next_action: {
    action_code: 'FIELD_DETECTOR_VALIDATION',
    title_en: 'Plan verified temporary turning-count validation',
    title_ru: 'Спланировать верифицированную временную проверку поворотных потоков',
    description_en: 'Verify baseline vehicle arrival rates and queue discharge dynamics prior to permanent controller programming.',
    description_ru: 'Проверка фактической интенсивности и динамики схода очередей перед перепрограммированием дорожных контроллеров.',
    priority: 'HIGH',
  },
  target_stakeholder: 'Tashkent City Department of Transport (Toshkent shahar Transport boshqarmasi)',
}

export function PilotWorkspace({
  language = 'en',
  t = {},
  onNavigateToDashboard,
  onNavigateToExplore,
  onOpenReport,
  onOpenCaseStudy,
}) {
  const isRu = language === 'ru'
  const [selectedPilot, setSelectedPilot] = useState(DEFAULT_PILOT_CASE)
  const [isLoading, setIsLoading] = useState(true)
  const [activeMechanism, setActiveMechanism] = useState('mechanism3')

  useEffect(() => {
    async function loadData() {
      setIsLoading(true)
      try {
        const pilots = await fetchPilotCases()
        if (pilots && pilots.length > 0) {
          setSelectedPilot(pilots[0])
        } else {
          setSelectedPilot(DEFAULT_PILOT_CASE)
        }
      } catch (err) {
        console.error('Failed to load pilot cases; showing an empty draft workspace:', err)
        setSelectedPilot(DEFAULT_PILOT_CASE)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [])


  const handleStatusChange = async (newStatus) => {
    if (!selectedPilot) return
    try {
      const updated = await updatePilotCase(selectedPilot.id, { status: newStatus })
      if (updated) {
        setSelectedPilot(updated)
      }
    } catch (e) {
      console.error('Failed to update pilot status:', e)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETED': return '#4ade80'
      case 'FIELD_VALIDATION': return '#38bdf8'
      case 'REVIEW': return '#fbbf24'
      case 'ANALYSIS': return '#a855f7'
      default: return '#94a3b8'
    }
  }

  const getStatusLabel = (status) => {
    if (!isRu) return status
    switch (status) {
      case 'DRAFT': return 'ЧЕРНОВИК'
      case 'ANALYSIS': return 'АНАЛИЗ'
      case 'REVIEW': return 'СОГЛАСОВАНИЕ'
      case 'FIELD_VALIDATION': return 'ПОЛЕВАЯ ВАЛИДАЦИЯ'
      case 'COMPLETED': return 'ЗАВЕРШЕНО'
      default: return status
    }
  }

  if (isLoading) {
    return (
      <div className="panel-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <span className="spinner" style={{ display: 'inline-block', marginBottom: '1rem' }} />
        <div>{isRu ? 'Загрузка муниципальных пилотных проектов…' : 'Loading municipal pilot cases…'}</div>
      </div>
    )
  }

  const pilot = selectedPilot || {}
  const nextAct = pilot.next_action || {}
  const baseline = pilot.baseline_summary || {}
  const recOption = pilot.recommended_option || {}
  const hasSimulationEvidence = Boolean(
    pilot.evidence_strength &&
    pilot.evidence_strength !== 'NOT_AVAILABLE' &&
    (Object.keys(baseline).length > 0 || Object.keys(recOption).length > 0)
  )
  const formatMetric = (value, suffix = '') => {
    const numericValue = Number(value)
    return Number.isFinite(numericValue) ? `${numericValue}${suffix}` : '—'
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.4rem' }}>
      {/* 1. Header Banner & Decision-Making Mechanisms Overview */}
      <div
        className="panel-card"
        style={{
          padding: '1.4rem 1.6rem',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.85) 100%)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          borderRadius: '16px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.2rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
              <span className="brand-mark">U</span>
              <span style={{ fontSize: '0.78rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                {isRu ? 'B2G ПИЛОТНАЯ ГОТОВНОСТЬ И ПОДДЕРЖКА РЕШЕНИЙ' : 'B2G PILOT READINESS & DECISION SUPPORT'}
              </span>
            </div>
            <h2 style={{ margin: '0 0 0.4rem 0', fontSize: '1.45rem', fontWeight: 800, color: '#fff' }}>
              {isRu ? 'Муниципальные пилотные проекты и аналитические обоснования' : 'Municipal Pilot Cases & Defensible Decision Briefs'}
            </h2>
            <p style={{ margin: 0, fontSize: '0.86rem', color: 'var(--text-secondary)', maxWidth: '750px', lineHeight: 1.45 }}>
              {isRu
                ? 'Платформа предоставляет 3 взаимосвязанных уровня поддержки принятия решений: от оперативной настройки сигналов до сценарного стресс-тестирования и подготовки обоснованного проекта пилота.'
                : 'UrbanMind provides 3 interconnected decision-support mechanisms: from real-time corridor signal tuning to scenario stress-testing and municipal pilot project preparation.'}
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span
              style={{
                background: `rgba(${pilot.status === 'FIELD_VALIDATION' ? '56, 189, 248' : '74, 222, 128'}, 0.15)`,
                border: `1px solid ${getStatusColor(pilot.status)}`,
                color: getStatusColor(pilot.status),
                borderRadius: '8px',
                padding: '0.45rem 0.85rem',
                fontSize: '0.82rem',
                fontWeight: 800,
                letterSpacing: '0.05em',
              }}
            >
              ● {getStatusLabel(pilot.status || 'FIELD_VALIDATION')}
            </span>
          </div>
        </div>

        {/* 3 Decision-Making Mechanisms Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.85rem' }}>
          {/* Mechanism 1 */}
          <div
            onClick={() => {
              setActiveMechanism('mechanism1')
              if (onNavigateToDashboard) onNavigateToDashboard()
            }}
            style={{
              background: activeMechanism === 'mechanism1' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(255, 255, 255, 0.03)',
              border: `1px solid ${activeMechanism === 'mechanism1' ? '#38bdf8' : 'rgba(255, 255, 255, 0.08)'}`,
              borderRadius: '10px',
              padding: '1rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ fontSize: '0.72rem', color: '#38bdf8', fontWeight: 800, textTransform: 'uppercase', marginBottom: '3px' }}>
              {isRu ? 'Механизм 1: Оперативный' : 'Mechanism 1: Operational'}
            </div>
            <strong style={{ fontSize: '0.92rem', color: '#fff', display: 'block', marginBottom: '4px' }}>
              {t.mechanism1Title || (isRu ? '1. Тактическая оптимизация сигналов' : '1. Tactical Signal Optimization')}
            </strong>
            <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              {t.mechanism1Desc || (isRu ? 'Интерактивная настройка фаз коридора и выбор политик (FLOW, ECO, BALANCED) на карте в реальном времени.' : 'Interactive multi-objective corridor timing and policy trade-offs (FLOW, ECO, BALANCED) on the live map.')}
            </p>
          </div>

          {/* Mechanism 2 */}
          <div
            onClick={() => {
              setActiveMechanism('mechanism2')
              if (onNavigateToExplore) onNavigateToExplore()
            }}
            style={{
              background: activeMechanism === 'mechanism2' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(255, 255, 255, 0.03)',
              border: `1px solid ${activeMechanism === 'mechanism2' ? '#38bdf8' : 'rgba(255, 255, 255, 0.08)'}`,
              borderRadius: '10px',
              padding: '1rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ fontSize: '0.72rem', color: '#a855f7', fontWeight: 800, textTransform: 'uppercase', marginBottom: '3px' }}>
              {isRu ? 'Механизм 2: Сценарный' : 'Mechanism 2: Scenario Analysis'}
            </div>
            <strong style={{ fontSize: '0.92rem', color: '#fff', display: 'block', marginBottom: '4px' }}>
              {t.mechanism2Title || (isRu ? '2. Матрица чувствительности сценариев' : '2. Scenario Sensitivity Matrix')}
            </strong>
            <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              {t.mechanism2Desc || (isRu ? 'Стресс-тестирование спроса (0.8x, 1.0x, 1.2x) и стохастическая проверка устойчивости по мульти-сидам.' : 'Systematic demand sweeps (0.8x, 1.0x, 1.2x) and multi-seed stochastic robustness testing.')}
            </p>
          </div>

          {/* Mechanism 3 */}
          <div
            onClick={() => setActiveMechanism('mechanism3')}
            style={{
              background: activeMechanism === 'mechanism3' ? 'rgba(74, 222, 128, 0.12)' : 'rgba(255, 255, 255, 0.03)',
              border: `1px solid ${activeMechanism === 'mechanism3' ? '#4ade80' : 'rgba(255, 255, 255, 0.08)'}`,
              borderRadius: '10px',
              padding: '1rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ fontSize: '0.72rem', color: '#4ade80', fontWeight: 800, textTransform: 'uppercase', marginBottom: '3px' }}>
              {isRu ? 'Механизм 3: Муниципальный B2G' : 'Mechanism 3: Municipal B2G'}
            </div>
            <strong style={{ fontSize: '0.92rem', color: '#fff', display: 'block', marginBottom: '4px' }}>
              {t.mechanism3Title || (isRu ? '3. Муниципальный пилотный проект' : '3. Municipal Pilot Case')}
            </strong>
            <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              {t.mechanism3Desc || (isRu ? 'Обоснованный проект пилота: проблема → политика → доказательства → калибровка → план действий.' : 'Defensible B2G project brief connecting problem → policy → evidence → calibration → action.')}
            </p>
          </div>
        </div>
      </div>

      {/* 2. Active Pilot Case Detail Card */}
      <div
        className="panel-card"
        style={{
          padding: '1.5rem',
          backgroundColor: 'var(--bg-base, #0b1329)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '16px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <span style={{ fontSize: '0.72rem', color: '#38bdf8', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
              {pilot.id || 'PILOT-TASHKENT-CENTRAL-01'}
            </span>
            <h3 style={{ margin: '2px 0 0 0', fontSize: '1.25rem', color: '#ffffff', fontWeight: 800 }}>
              {isRu ? (pilot.title_ru || pilot.title) : pilot.title}
            </h3>
          </div>

          {/* Stepper Status Buttons */}
          <div style={{ display: 'flex', gap: '0.35rem', background: 'rgba(0,0,0,0.3)', padding: '0.3rem', borderRadius: '8px' }}>
            {['DRAFT', 'ANALYSIS', 'REVIEW', 'FIELD_VALIDATION', 'COMPLETED'].map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => handleStatusChange(st)}
                style={{
                  background: pilot.status === st ? getStatusColor(st) : 'transparent',
                  color: pilot.status === st ? '#0f172a' : 'var(--text-muted)',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '0.3rem 0.6rem',
                  fontSize: '0.74rem',
                  fontWeight: pilot.status === st ? 800 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {getStatusLabel(st)}
              </button>
            ))}
          </div>
        </div>

        {/* Problem Statement & Objective */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <strong style={{ fontSize: '0.78rem', color: '#f87171', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
              ⚠️ {isRu ? 'Формулировка проблемы' : 'Problem Statement'}
            </strong>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              {isRu ? (pilot.problem_statement_ru || pilot.problem_statement) : pilot.problem_statement}
            </p>
          </div>

          <div style={{ background: 'rgba(56, 189, 248, 0.04)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(56, 189, 248, 0.15)' }}>
            <strong style={{ fontSize: '0.78rem', color: '#38bdf8', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
              🎯 {isRu ? 'Цель и политика пилота' : 'Objective & Active Policy'}
            </strong>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              {isRu ? (pilot.objective_ru || pilot.objective) : pilot.objective}
            </p>
          </div>
        </div>

        {/* Baseline vs Recommended Candidate Strip */}
        <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '1.1rem', borderRadius: '12px', border: '1px solid rgba(56, 189, 248, 0.25)', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                {isRu ? 'Кандидат для полевой проверки' : 'Candidate for Field Validation'}
              </span>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#38bdf8' }}>
                {hasSimulationEvidence
                  ? (isRu ? (recOption.label_ru || recOption.label) : recOption.label)
                  : (isRu ? 'Симуляционный кандидат недоступен' : 'No simulated candidate available')}
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <span style={{ background: hasSimulationEvidence ? 'rgba(74, 222, 128, 0.15)' : 'rgba(148, 163, 184, 0.15)', color: hasSimulationEvidence ? '#4ade80' : '#94a3b8', padding: '0.3rem 0.6rem', borderRadius: '6px', fontSize: '0.78rem', fontWeight: 700 }}>
                🛡️ {hasSimulationEvidence
                  ? `${isRu ? 'Доказательность' : 'Evidence'}: ${pilot.evidence_strength}`
                  : (isRu ? 'Доказательность: НЕДОСТУПНО' : 'Evidence: NOT AVAILABLE')}
              </span>
              <span style={{ background: 'rgba(217, 119, 6, 0.15)', color: '#fbbf24', padding: '0.3rem 0.6rem', borderRadius: '6px', fontSize: '0.78rem', fontWeight: 700 }}>
                ⚙️ {pilot.calibration_status || 'UNCALIBRATED'}
              </span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem' }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.7rem', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{isRu ? 'Базовая задержка' : 'Baseline Delay'}</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>{formatMetric(baseline.average_waiting_seconds, ' s')}</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.7rem', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{isRu ? 'Ожидаемое снижение' : 'Estimated Reduction'}</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#4ade80' }}>{formatMetric(recOption.expected_delay_reduction_pct, '%')}</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.7rem', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{isRu ? 'Снижение выбросов CO₂' : 'CO₂ Reduction'}</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#4ade80' }}>{formatMetric(recOption.expected_co2_reduction_pct, '%')}</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.7rem', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{isRu ? 'Базовый поток' : 'Baseline Flow'}</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#38bdf8' }}>{formatMetric(baseline.throughput_vehicles_per_hour, ' veh/h')}</div>
            </div>
          </div>
        </div>

        {/* Recommended Next Action Card */}
        <div
          style={{
            background: 'rgba(56, 189, 248, 0.08)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderLeft: '4px solid #38bdf8',
            borderRadius: '10px',
            padding: '1rem 1.2rem',
            marginBottom: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
            <strong style={{ fontSize: '0.82rem', color: '#38bdf8', textTransform: 'uppercase' }}>
              🎯 {isRu ? 'Рекомендуемый следующий шаг (Полевая валидация):' : 'Recommended Next Action (Field Validation):'}
            </strong>
            <span style={{ fontSize: '0.72rem', background: '#38bdf8', color: '#0f172a', fontWeight: 800, padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
              {nextAct.priority || 'HIGH'} PRIORITY
            </span>
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>
            {isRu ? nextAct.title_ru : nextAct.title_en}
          </div>
          <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
            {isRu ? nextAct.description_ru : nextAct.description_en}
          </p>
        </div>

        {/* Action Buttons & Municipal Authority Disclaimer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', maxWidth: '600px' }}>
            ⚖️ <strong>{isRu ? 'Оговорка:' : 'Disclaimer:'}</strong>{' '}
            {t.municipalDisclaimer || (isRu
              ? 'UrbanMind формирует аналитические рекомендации на основе моделирования. Окончательное решение и полномочия по внедрению остаются за ответственным органом управления транспортом.'
              : 'UrbanMind provides simulation-supported analytical recommendations. Final municipal decision and implementation authority rests with the responsible transport agency.')}
          </div>

          <div style={{ display: 'flex', gap: '0.6rem' }}>
            {onOpenCaseStudy && (
              <button
                type="button"
                className="ghost-button"
                onClick={onOpenCaseStudy}
                style={{ fontSize: '0.84rem', padding: '0.55rem 1.1rem', borderColor: '#38bdf8', color: '#38bdf8' }}
              >
                📖 {isRu ? 'Канонический кейс-стади #001' : 'Canonical Case Study #001'}
              </button>
            )}
            {onOpenReport && (
              <button
                type="button"
                className="accent"
                onClick={onOpenReport}
                style={{ fontSize: '0.84rem', padding: '0.55rem 1.1rem' }}
              >
                📋 {isRu ? 'Открыть полный отчет о решении' : 'Open Full Decision Report'}
              </button>
            )}
          </div>

        </div>
      </div>
    </div>
  )
}
