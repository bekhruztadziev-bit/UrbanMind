"""IQAir provider (optional secondary source).

Fetches real-time air quality data from the IQAir API.
This provider is optional — it requires IQAIR_API_KEY in the environment.

API documentation: https://www.iqair.com/commercial/air-quality-monitors/airvisual-platform/api
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from app.services.environment.models import (
    EnvironmentalObservation,
    determine_data_quality,
)

logger = logging.getLogger(__name__)

IQAIR_BASE_URL = "https://api.airvisual.com/v2"


def _get_key() -> Optional[str]:
    """Read IQAir API key from environment."""
    return os.environ.get("IQAIR_API_KEY")


def fetch_observation() -> Optional[EnvironmentalObservation]:
    """Fetch current observation from IQAir for Tashkent.

    Returns None on any failure (missing key, network error, bad response).
    Never raises exceptions.
    """
    key = _get_key()
    if not key:
        logger.debug("IQAIR_API_KEY not set; skipping IQAir provider")
        return None

    url = f"{IQAIR_BASE_URL}/nearest_city?lat=41.2995&lon=69.2401&key={key}"

    try:
        import httpx

        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            logger.warning("IQAir returned non-success status: %s", data.get("status"))
            return None

        payload = data.get("data", {})
        current = payload.get("current", {})
        pollution = current.get("pollution", {})
        weather = current.get("weather", {})

        # Parse timestamp
        obs_time = None
        ts_str = pollution.get("ts")
        if ts_str:
            try:
                obs_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        quality = determine_data_quality(obs_time)

        # IQAir provides US AQI and main pollutant
        aqi = pollution.get("aqius")
        main_pol = pollution.get("mainus")

        # IQAir provides limited pollutant breakdown in free tier
        # PM2.5 concentration is available as p2.conc
        pm25 = None
        p2 = pollution.get("p2")  # Some responses include this
        if isinstance(p2, dict):
            pm25 = p2.get("conc")

        return EnvironmentalObservation(
            source="IQAir",
            station=f"{payload.get('city', 'Tashkent')}, {payload.get('country', 'Uzbekistan')}",
            timestamp=obs_time,
            latitude=payload.get("location", {}).get("coordinates", [None, None])[1] if payload.get("location") else None,
            longitude=payload.get("location", {}).get("coordinates", [None, None])[0] if payload.get("location") else None,
            pm25=pm25,
            aqi=int(aqi) if aqi is not None else None,
            dominant_pollutant=main_pol,
            temperature=weather.get("tp"),
            humidity=weather.get("hu"),
            wind=weather.get("ws"),
            pressure=weather.get("pr"),
            data_quality=quality,
        )

    except Exception as exc:
        logger.warning("IQAir provider failed: %s", exc)
        return None
