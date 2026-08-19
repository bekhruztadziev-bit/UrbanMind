import { useState, useEffect } from 'react';
import { fetchEnvironmentCurrent, fetchEnvironmentStations } from '../api/client';

export function useEnvironment() {
  const [currentData, setCurrentData] = useState(null);
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function loadData() {
      try {
        setLoading(true);
        const [currentObs, stationsList] = await Promise.all([
          fetchEnvironmentCurrent(),
          fetchEnvironmentStations(),
        ]);

        if (mounted) {
          setCurrentData(currentObs);
          setStations(stationsList);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          console.warn('Failed to load environmental data:', err);
          setError(err.message || 'Failed to load environmental data');
          // Fallback to unavailable state
          setCurrentData({ data_quality: 'UNAVAILABLE' });
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadData();

    // Refresh data every 5 minutes
    const intervalId = setInterval(loadData, 5 * 60 * 1000);

    return () => {
      mounted = false;
      clearInterval(intervalId);
    };
  }, []);

  return {
    currentData,
    stations,
    loading,
    error,
    isAvailable: currentData?.data_quality !== 'UNAVAILABLE' && currentData?.data_quality !== undefined,
  };
}
