import React, { useEffect, useRef } from 'react';
import { animateHighlight, animateTokenFlash, MOTION } from '../../utils/motion';

export function EnvironmentPanel({ t, language, envData }) {
  const panelRef = useRef(null);
  const badgeRef = useRef(null);
  const prevQualityRef = useRef(envData?.currentData?.data_quality);

  useEffect(() => {
    if (envData?.currentData?.data_quality !== prevQualityRef.current) {
      prevQualityRef.current = envData?.currentData?.data_quality;
      if (panelRef.current) animateHighlight(panelRef.current, { duration: MOTION.normal });
      if (badgeRef.current) animateTokenFlash(badgeRef.current);
    }
  }, [envData]);

  if (!envData) return null;

  const { currentData, isAvailable } = envData;

  const renderStatusBadge = () => {
    if (!currentData || !isAvailable) {
      return <span ref={badgeRef} className="env-status-badge unavailable">{t.envUnavailable || 'Unavailable'}</span>;
    }
    
    switch (currentData.data_quality) {
      case 'LIVE': return <span ref={badgeRef} className="env-status-badge live">{t.envLive || 'Live'}</span>;
      case 'RECENT': return <span ref={badgeRef} className="env-status-badge recent">{t.envRecent || 'Recent'}</span>;
      case 'STALE': return <span ref={badgeRef} className="env-status-badge stale">{t.envStale || 'Stale'}</span>;
      default: return <span ref={badgeRef} className="env-status-badge unavailable">{t.envUnavailable || 'Unavailable'}</span>;
    }
  };

  const getAQIColor = (aqi) => {
    if (aqi === null || aqi === undefined) return '#94a3b8';
    if (aqi <= 50) return '#10b981'; // Good (Green)
    if (aqi <= 100) return '#f59e0b'; // Moderate (Yellow)
    if (aqi <= 150) return '#f97316'; // Unhealthy for Sensitive Groups (Orange)
    if (aqi <= 200) return '#ef4444'; // Unhealthy (Red)
    if (aqi <= 300) return '#a855f7'; // Very Unhealthy (Purple)
    return '#881337'; // Hazardous (Maroon)
  };

  const formatNumber = (num, decimals = 1) => {
    if (num === null || num === undefined) return '--';
    return Number(num).toFixed(decimals);
  };

  const formatTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString(language === 'ru' ? 'ru-RU' : 'en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="panel-card environment-panel full-width-card mt-3" ref={panelRef}>
      <div className="env-header">
        <div className="env-title-group">
          <span className="eyebrow">{t.tashkent || 'TASHKENT'}</span>
          <div className="env-title-row">
            <h2>{t.environmentTitle || 'CURRENT ENVIRONMENT'}</h2>
            <span className="provenance-badge observed">OBSERVED</span>
          </div>
        </div>
        {renderStatusBadge()}
      </div>

      <div className="env-metrics-grid">
        <div className="env-metric-item">
          <span className="label">PM2.5</span>
          <div className="value-group">
            <span className="value">{formatNumber(currentData?.pm25)}</span>
            <span className="unit">μg/m³</span>
          </div>
        </div>
        <div className="env-metric-item">
          <span className="label">PM10</span>
          <div className="value-group">
            <span className="value">{formatNumber(currentData?.pm10)}</span>
            <span className="unit">μg/m³</span>
          </div>
        </div>
        <div className="env-metric-item">
          <span className="label">AQI</span>
          <div className="value-group">
            <span className="value" style={{ color: getAQIColor(currentData?.aqi) }}>
              {currentData?.aqi ?? '--'}
            </span>
          </div>
        </div>
      </div>

      <div className="env-footer">
        <div className="env-footer-item">
          <span className="footer-label">{t.source || 'Source'}</span>
          <span className="footer-value">
            {isAvailable ? currentData.source : t.envOfflineFallbackText || 'Data unavailable'}
          </span>
        </div>
        <div className="env-footer-item right-align">
          <span className="footer-label">{t.updated || 'Updated'}</span>
          <span className="footer-value">
            {isAvailable ? formatTime(currentData.timestamp) : '--:--'}
          </span>
        </div>
      </div>
    </div>
  );
}
