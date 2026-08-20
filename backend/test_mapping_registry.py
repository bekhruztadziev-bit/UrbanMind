import pytest

from app.services.calibration.mappings import MovementMapping, MovementMappingRegistry
from app.services.simulation.network_inspector import get_network_identity, inspect_mapping_candidate


def _mapping(**changes):
    identity = get_network_identity()
    values = dict(
        mapping_id="mapping-v1", city_id="city", district_id="district", corridor_id="corridor",
        intersection_id="ix", intersection_name="Intersection", approach_id="north", approach_name="North",
        movement="through", incoming_edge="not-a-real-edge", outgoing_edge="not-a-real-outgoing", lane_ids=(),
        signal_id=None, enabled=True, notes="test", network_version=identity["network_version"],
        configuration_hash=identity["network_sha256"], verification_status="ENABLED",
        verification_method="TEST_FIXTURE", verified_at="2026-08-20T00:00:00Z", verified_by="test",
    )
    values.update(changes)
    return MovementMapping(**values)


def test_unverified_mapping_is_not_eligible_for_calibration():
    registry = MovementMappingRegistry([_mapping(verification_status="NETWORK_VERIFIED", enabled=False)])
    assert registry.lookup("ix", "north", "through") is None
    assert registry.coverage()["enabled_movement_count"] == 0


def test_enabled_verified_mapping_is_eligible_and_identity_is_immutable():
    mapping = _mapping()
    registry = MovementMappingRegistry([mapping])
    assert registry.lookup("ix", "north", "through") is mapping
    with pytest.raises(ValueError, match="Duplicate movement mapping"):
        MovementMappingRegistry([mapping, _mapping(incoming_edge="changed")])


def test_network_candidate_mismatch_is_reported_not_approved():
    result = inspect_mapping_candidate(_mapping(configuration_hash="wrong-hash"))
    assert result["network_version_matches"] is True
    assert result["network_hash_matches"] is False
    assert result["edge_connection_exists"] is False
    assert result["approval"] == "NOT_APPROVED_AUTOMATICALLY"
