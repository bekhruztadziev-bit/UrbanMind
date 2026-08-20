import pytest
from app.services.spatial.hierarchy import (
    get_spatial_hierarchy,
    get_default_spatial_scope,
    get_cross_district_context,
    find_intersection_by_signal_id,
    TASHKENT_CITY,
    CENTRAL_DISTRICT,
    CENTRAL_CORRIDOR,
    TASHKENT_INTERSECTIONS,
)


def test_spatial_hierarchy_integrity():
    """Verify that City -> District -> Corridor -> Intersection hierarchy is properly formed."""
    city = get_spatial_hierarchy()
    assert city["id"] == "tashkent"
    assert city["name"] == "Tashkent"
    assert "districts" in city
    assert len(city["districts"]) >= 1

    central = next(d for d in city["districts"] if d["id"] == "central_tashkent")
    assert central["city_id"] == "tashkent"
    assert len(central["corridors"]) >= 1

    corridor = central["corridors"][0]
    assert corridor["id"] == "central_corridor"
    assert corridor["district_id"] == "central_tashkent"
    assert len(corridor["intersections"]) == 6

    # Demonstration labels are not represented as verified SUMO signal links.
    assert all(inter["id"].startswith("demo_signal_group_") for inter in corridor["intersections"])
    assert all(inter["signal_ids"] == [] for inter in corridor["intersections"])


def test_default_spatial_scope():
    """Verify default scope points to Central Tashkent Corridor."""
    scope = get_default_spatial_scope()
    assert scope["level"] == "corridor"
    assert scope["id"] == "central_corridor"
    assert scope["city_name"] == "Tashkent"
    assert scope["district_name"] == "Unverified demonstration district"
    assert scope["spatial_provenance"] == "PRODUCT_DEMO_LABEL"


def test_cross_district_context():
    """Verify cross-district context has primary and neighboring scopes."""
    context = get_cross_district_context()
    assert context["primary_scope"]["id"] == "central_corridor"
    assert context["neighboring_scopes"] == []
    assert context["spillover_effects"]["status"] == "NOT_EVALUATED"


def test_find_intersection_by_signal():
    """Verify intersection lookup by signal ID."""
    assert find_intersection_by_signal_id("cluster_1") is None
    assert find_intersection_by_signal_id("non_existent_signal") is None
