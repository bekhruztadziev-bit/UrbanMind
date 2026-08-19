"""WAQI (World Air Quality Index) provider.

Fetches real-time air quality data from the WAQI/AQICN API.
WAQI aggregates data from official monitoring networks including Uzhydromet.

API documentation: https://aqicn.org/json-api/doc/
Token registration: https://aqicn.org/data-platform/token/

Source attribution format:
    "Uzhydromet via WAQI" when the underlying station is operated by Uzhydromet.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from app.services.environment.models import (
    DataQuality,
    EnvironmentalObservation,
    determine_data_quality,
)

logger = logging.getLogger(__name__)

WAQI_BASE_URL = "https://api.waqi.info"

# Known Tashkent station IDs on WAQI
TASHKENT_STATIONS = {
    "chilanzar": {"waqi_id": "@14722", "name": "Chilanzar", "lat": 41.2856, "lng": 69.2128},
}

DEFAULT_STATION = "chilanzar"

# Tashkent center for geo-based query fallback
TASHKENT_CENTER = (41.2995, 69.2401)


def _get_token() -> Optional[str]:
    """Read WAQI API token from environment."""
    return os.environ.get("WAQI_API_TOKEN") or os.environ.get("WAQI_TOKEN")


def _parse_waqi_response(data: dict) -> Optional[EnvironmentalObservation]:
    """Parse a WAQI API JSON response into an EnvironmentalObservation.

    WAQI response structure:
    {
      "status": "ok",
      "data": {
        "aqi": 72,
        "idx": 14722,
        "city": {"name": "Tashkent, Chilanzar", "geo": [41.28, 69.21]},
        "dominentpol": "pm25",
        "iaqi": {
          "pm25": {"v": 33.2},
          "pm10": {"v": 90},
          "no2": {"v": 5.5},
          ...
        },
        "time": {"iso": "2024-01-01T12:00:00+05:00"},
        "attributions": [{"name": "Uzhydromet", ...}]
      }
    }
    """
    if not data or data.get("status") != "ok":
        return None

    payload = data.get("data")
    if not payload or not isinstance(payload, dict):
        return None

    # Parse observation timestamp
    time_info = payload.get("time", {})
    obs_time = None
    if time_info.get("iso"):
        try:
            obs_time = datetime.fromisoformat(time_info["iso"])
            if obs_time.tzinfo is None:
                obs_time = obs_time.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass

    # Parse station info
    city_info = payload.get("city", {})
    station_name = city_info.get("name", "Unknown")
    geo = city_info.get("geo", [None, None])
    lat = float(geo[0]) if geo and len(geo) >= 2 and geo[0] is not None else None
    lng = float(geo[1]) if geo and len(geo) >= 2 and geo[1] is not None else None

    # Determine source attribution
    attributions = payload.get("attributions", [])
    source_names = [a.get("name", "") for a in attributions if a.get("name")]
    is_uzhydromet = any("uzhydromet" in n.lower() or "meteo" in n.lower() for n in source_names)
    source = "Uzhydromet via WAQI" if is_uzhydromet else "WAQI"

    # Parse individual pollutant values
    iaqi = payload.get("iaqi", {})

    def _val(key: str) -> Optional[float]:
        entry = iaqi.get(key)
        if entry and isinstance(entry, dict) and entry.get("v") is not None:
            try:
                return float(entry["v"])
            except (ValueError, TypeError):
                return None
        return None

    aqi_raw = payload.get("aqi")
    aqi = int(aqi_raw) if aqi_raw is not None and str(aqi_raw).strip() != "-" else None

    quality = determine_data_quality(obs_time)

    return EnvironmentalObservation(
        source=source,
        station=station_name,
        timestamp=obs_time,
        latitude=lat,
        longitude=lng,
        pm25=_val("pm25"),
        pm10=_val("pm10"),
        no2=_val("no2"),
        so2=_val("so2"),
        o3=_val("o3"),
        co=_val("co"),
        aqi=aqi,
        dominant_pollutant=payload.get("dominentpol"),
        temperature=_val("t"),
        humidity=_val("h"),
        wind=_val("w"),
        pressure=_val("p"),
        data_quality=quality,
    )


def fetch_observation(station_key: str = DEFAULT_STATION) -> Optional[EnvironmentalObservation]:
    """Fetch current observation from WAQI for Tashkent.

    Tries Chilanzar station (@14722), then city feed 'tashkent', then geo coordinates.
    Returns None on total failure (missing token, network error, bad response).
    Never raises exceptions — all errors are logged and absorbed.
    """
    token = _get_token()
    if not token or token == "your-waqi-api-token-here":
        logger.info("WAQI_API_TOKEN not set or placeholder; skipping WAQI provider")
        return None

    feed_endpoints = [
        f"{WAQI_BASE_URL}/feed/@14722/?token={token}",
        f"{WAQI_BASE_URL}/feed/tashkent/?token={token}",
        f"{WAQI_BASE_URL}/feed/geo:41.2995;69.2401/?token={token}",
    ]

    import httpx

    for url in feed_endpoints:
        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    observation = _parse_waqi_response(data)
                    if observation and (observation.aqi is not None or observation.pm25 is not None):
                        logger.info(
                            "WAQI observation success: station=%s aqi=%s pm25=%s quality=%s",
                            observation.station,
                            observation.aqi,
                            observation.pm25,
                            observation.data_quality,
                        )
                        return observation
        except Exception as exc:
            logger.warning("WAQI provider attempt failed for %s: %s", url, exc)

    return None

