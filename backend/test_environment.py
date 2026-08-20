import pytest
from app.services.environment.models import EnvironmentalObservation
from app.services.environment.provider import get_current_observation, invalidate_cache

def test_environment_provider_offline(monkeypatch):
    # Unit tests must not silently turn into live external API probes merely
    # because a developer has configured credentials locally.
    import app.services.environment.waqi_provider as waqi_provider
    import app.services.environment.iqair_provider as iqair_provider
    invalidate_cache()
    monkeypatch.setattr(waqi_provider, "fetch_observation", lambda: None)
    monkeypatch.setattr(iqair_provider, "fetch_observation", lambda: None)
    obs = get_current_observation()
    
    assert obs is not None
    assert obs.data_quality in ["LIVE", "RECENT", "STALE", "UNAVAILABLE"]
    if obs.data_quality == "UNAVAILABLE":
        assert obs.aqi is None
        assert obs.pm25 is None
        assert obs.source == "none"
    else:
        assert obs.source is not None
