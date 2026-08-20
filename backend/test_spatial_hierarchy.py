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

    # Verify all 6 signal clusters are present
    signal_ids = {inter["traffic_light_id"] for inter in corridor["intersections"]}
    assert signal_ids == {"cluster_1", "cluster_2", "cluster_3", "cluster_4", "cluster_5", "cluster_6"}


def test_default_spatial_scope():
    """Verify default scope points to Central Tashkent Corridor."""
    scope = get_default_spatial_scope()
    assert scope["level"] == "corridor"
    assert scope["id"] == "central_corridor"
    assert scope["city_name"] == "Tashkent"
    assert scope["district_name"] == "Mirzo Ulugbek / Yunusabad District"


def test_cross_district_context():
    """Verify cross-district context has primary and neighboring scopes."""
    context = get_cross_district_context()
    assert context["primary_scope"]["id"] == "central_corridor"
    assert len(context["neighboring_scopes"]) >= 2
    neighbor_ids = [n["id"] for n in context["neighboring_scopes"]]
    assert "chilanzar_district" in neighbor_ids
    assert "yakkasaray_district" in neighbor_ids
    assert "spillover_effects" in context


def test_find_intersection_by_signal():
    """Verify intersection lookup by signal ID."""
    inter = find_intersection_by_signal_id("cluster_1")
    assert inter is not None
    assert inter["name"] == "Main Square"
    assert inter["latitude"] == 41.3168
    assert inter["longitude"] == 69.2666

    inter6 = find_intersection_by_signal_id("cluster_6")
    assert inter6 is not None
    assert inter6["name"] == "Bus Terminal Link"

    assert find_intersection_by_signal_id("non_existent_signal") is None
