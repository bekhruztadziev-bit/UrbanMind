"""Unified environmental data provider with caching.

Provider priority: WAQI → IQAir → cached last-known → UNAVAILABLE.

Cache behaviour
---------------
- In-memory cache with configurable TTL (default 300 s / 5 minutes).
- Thread-safe via threading.Lock.
- On cache miss or expiry, providers are queried in priority order.
- On total provider failure, the last-known observation is returned with
  its original data_quality re-evaluated for staleness.
- Never fabricates environmental values. If no data has ever been obtained,
  returns an UNAVAILABLE observation with all values set to None.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Any, List, Optional

from app.services.environment.models import (
    DataQuality,
    EnvironmentalObservation,
    StationInfo,
    determine_data_quality,
)

logger = logging.getLogger(__name__)

# Cache TTL in seconds
CACHE_TTL_SECONDS = 300  # 5 minutes

# Known Tashkent monitoring stations (real locations)
TASHKENT_MONITORING_STATIONS: List[StationInfo] = [
    StationInfo(
        id="uzhydromet_chilanzar",
        name="Chilanzar",
        latitude=41.2856,
        longitude=69.2128,
        source="Uzhydromet",
    ),
    StationInfo(
        id="uzhydromet_tashkent_center",
        name="Tashkent Center (Amir Temur)",
        latitude=41.3111,
        longitude=69.2797,
        source="Uzhydromet",
    ),
    StationInfo(
        id="uzhydromet_sergeli",
        name="Sergeli",
        latitude=41.2275,
        longitude=69.2199,
        source="Uzhydromet",
    ),
    StationInfo(
        id="uzhydromet_olmazor",
        name="Olmazor",
        latitude=41.3377,
        longitude=69.2150,
        source="Uzhydromet",
    ),
    StationInfo(
        id="uzhydromet_yakkasaray",
        name="Yakkasaray",
        latitude=41.2887,
        longitude=69.2864,
        source="Uzhydromet",
    ),
]

# ── Cache state ──────────────────────────────────────────────────────────

_cache_lock = threading.Lock()
_cached_observation: Optional[EnvironmentalObservation] = None
_cache_timestamp: float = 0.0


def _is_cache_valid() -> bool:
    return _cached_observation is not None and (time.monotonic() - _cache_timestamp) < CACHE_TTL_SECONDS


def _update_cache(obs: EnvironmentalObservation) -> None:
    global _cached_observation, _cache_timestamp
    _cached_observation = obs
    _cache_timestamp = time.monotonic()


def _make_unavailable() -> EnvironmentalObservation:
    """Return a clean UNAVAILABLE observation with no fabricated values."""
    return EnvironmentalObservation(
        source="none",
        station="none",
        data_quality="UNAVAILABLE",
    )


# ── Public API ───────────────────────────────────────────────────────────

def get_current_observation() -> EnvironmentalObservation:
    """Return the best available environmental observation.

    Priority: cached (if fresh) → WAQI → IQAir → stale cache → UNAVAILABLE.
    Thread-safe. Never raises.
    """
    global _cached_observation, _cache_timestamp

    with _cache_lock:
        if _is_cache_valid():
            return _cached_observation  # type: ignore[return-value]

    # Cache miss or expired — try providers
    observation = None

    # 1. Try WAQI
    try:
        from app.services.environment.waqi_provider import fetch_observation as waqi_fetch
        observation = waqi_fetch()
    except Exception as exc:
        logger.warning("WAQI provider import/call error: %s", exc)

    # 2. Try IQAir if WAQI failed
    if observation is None:
        try:
            from app.services.environment.iqair_provider import fetch_observation as iqair_fetch
            observation = iqair_fetch()
        except Exception as exc:
            logger.warning("IQAir provider import/call error: %s", exc)

    # 3. Update cache if we got something
    if observation is not None:
        with _cache_lock:
            _update_cache(observation)
        return observation

    # 4. Return stale cache if available (with re-evaluated quality)
    with _cache_lock:
        if _cached_observation is not None:
            stale = _cached_observation
            stale.data_quality = determine_data_quality(stale.timestamp)
            return stale

    # 5. Nothing at all
    return _make_unavailable()


def get_tashkent_stations() -> List[Dict[str, Any]]:
    """Return the list of known Tashkent monitoring stations."""
    return [s.to_dict() for s in TASHKENT_MONITORING_STATIONS]


def invalidate_cache() -> None:
    """Clear the observation cache. Useful for testing."""
    global _cached_observation, _cache_timestamp
    with _cache_lock:
        _cached_observation = None
        _cache_timestamp = 0.0
