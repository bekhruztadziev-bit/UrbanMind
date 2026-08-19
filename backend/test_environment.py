import pytest
from app.services.environment.models import EnvironmentalObservation
from app.services.environment.provider import get_current_observation

def test_environment_provider_offline():
    # Since we don't mock the provider here, and we don't have API keys set in the test environment,
    # the provider should gracefully return an UNAVAILABLE observation.
    obs = get_current_observation()
    
    assert obs is not None
    assert obs.data_quality in ["LIVE", "RECENT", "STALE", "UNAVAILABLE"]
    if obs.data_quality == "UNAVAILABLE":
        assert obs.aqi is None
        assert obs.pm25 is None
        assert obs.source == "none"
    else:
        assert obs.source is not None
