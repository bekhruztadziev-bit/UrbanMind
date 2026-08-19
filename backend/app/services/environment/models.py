"""Environmental observation data models.

Freshness thresholds
--------------------
LIVE:        observation_age < 30 minutes
RECENT:      observation_age < 3 hours
STALE:       observation_age < 24 hours
UNAVAILABLE: observation_age >= 24 hours, or no data available

These thresholds are documented in docs/methodology/ENVIRONMENTAL_DATA_AND_MODEL.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional


DataQuality = Literal["LIVE", "RECENT", "STALE", "UNAVAILABLE"]

# Thresholds in seconds
FRESHNESS_LIVE_SECONDS = 30 * 60        # 30 minutes
FRESHNESS_RECENT_SECONDS = 3 * 60 * 60  # 3 hours
FRESHNESS_STALE_SECONDS = 24 * 60 * 60  # 24 hours


class StationInfo:
    """A known environmental monitoring station."""

    __slots__ = ("id", "name", "latitude", "longitude", "source", "city")

    def __init__(
        self,
        *,
        id: str,
        name: str,
        latitude: float,
        longitude: float,
        source: str = "Uzhydromet",
        city: str = "Tashkent",
    ):
        self.id = id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.source = source
        self.city = city

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "source": self.source,
            "city": self.city,
        }


class EnvironmentalObservation:
    """A single environmental observation from a monitoring source.

    All concentration values are in µg/m³ unless otherwise noted.
    AQI uses the US EPA scale (0–500) as reported by WAQI.
    Temperature in °C, humidity in %, wind in m/s, pressure in hPa.
    """

    def __init__(
        self,
        *,
        source: str,
        station: str,
        timestamp: Optional[datetime] = None,
        retrieved_at: Optional[datetime] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        pm25: Optional[float] = None,
        pm10: Optional[float] = None,
        no2: Optional[float] = None,
        so2: Optional[float] = None,
        o3: Optional[float] = None,
        co: Optional[float] = None,
        aqi: Optional[int] = None,
        dominant_pollutant: Optional[str] = None,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        wind: Optional[float] = None,
        pressure: Optional[float] = None,
        data_quality: DataQuality = "UNAVAILABLE",
    ):
        self.source = source
        self.station = station
        self.timestamp = timestamp
        self.retrieved_at = retrieved_at or datetime.now(timezone.utc)
        self.latitude = latitude
        self.longitude = longitude
        self.pm25 = pm25
        self.pm10 = pm10
        self.no2 = no2
        self.so2 = so2
        self.o3 = o3
        self.co = co
        self.aqi = aqi
        self.dominant_pollutant = dominant_pollutant
        self.temperature = temperature
        self.humidity = humidity
        self.wind = wind
        self.pressure = pressure
        self.data_quality = data_quality

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "station": self.station,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "pm25": self.pm25,
            "pm10": self.pm10,
            "no2": self.no2,
            "so2": self.so2,
            "o3": self.o3,
            "co": self.co,
            "aqi": self.aqi,
            "dominant_pollutant": self.dominant_pollutant,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "wind": self.wind,
            "pressure": self.pressure,
            "data_quality": self.data_quality,
        }


def determine_data_quality(observation_time: Optional[datetime]) -> DataQuality:
    """Determine freshness quality based on observation timestamp."""
    if observation_time is None:
        return "UNAVAILABLE"

    now = datetime.now(timezone.utc)
    # Ensure observation_time is timezone-aware
    if observation_time.tzinfo is None:
        observation_time = observation_time.replace(tzinfo=timezone.utc)

    age_seconds = (now - observation_time).total_seconds()

    if age_seconds < 0:
        # Future timestamp — treat as live (clock skew)
        return "LIVE"
    if age_seconds < FRESHNESS_LIVE_SECONDS:
        return "LIVE"
    if age_seconds < FRESHNESS_RECENT_SECONDS:
        return "RECENT"
    if age_seconds < FRESHNESS_STALE_SECONDS:
        return "STALE"
    return "UNAVAILABLE"
