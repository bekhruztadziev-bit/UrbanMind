from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.services.spatial.models import (
    CityEntity,
    DistrictEntity,
    CorridorEntity,
    IntersectionEntity,
    SpatialScopeRef,
    CrossDistrictContext,
)

# Canonical Tashkent Central Corridor Intersections
TASHKENT_INTERSECTIONS: List[IntersectionEntity] = [
    {
        "id": "intersection_1",
        "corridor_id": "central_corridor",
        "name": "Main Square",
        "name_ru": "Главная площадь",
        "latitude": 41.3168,
        "longitude": 69.2666,
        "coords": (41.3168, 69.2666),
        "traffic_light_id": "cluster_1",
        "signal_ids": ["cluster_1"],
    },
    {
        "id": "intersection_2",
        "corridor_id": "central_corridor",
        "name": "School Junction",
        "name_ru": "Школьный перекресток",
        "latitude": 41.3182,
        "longitude": 69.2684,
        "coords": (41.3182, 69.2684),
        "traffic_light_id": "cluster_2",
        "signal_ids": ["cluster_2"],
    },
    {
        "id": "intersection_3",
        "corridor_id": "central_corridor",
        "name": "Clinic Roundabout",
        "name_ru": "Кольцо у поликлиники",
        "latitude": 41.3157,
        "longitude": 69.2692,
        "coords": (41.3157, 69.2692),
        "traffic_light_id": "cluster_3",
        "signal_ids": ["cluster_3"],
    },
    {
        "id": "intersection_4",
        "corridor_id": "central_corridor",
        "name": "Market Edge",
        "name_ru": "Рыночный узел",
        "latitude": 41.3149,
        "longitude": 69.2638,
        "coords": (41.3149, 69.2638),
        "traffic_light_id": "cluster_4",
        "signal_ids": ["cluster_4"],
    },
    {
        "id": "intersection_5",
        "corridor_id": "central_corridor",
        "name": "North Residential Corridor",
        "name_ru": "Северный жилой коридор",
        "latitude": 41.3199,
        "longitude": 69.2718,
        "coords": (41.3199, 69.2718),
        "traffic_light_id": "cluster_5",
        "signal_ids": ["cluster_5"],
    },
    {
        "id": "intersection_6",
        "corridor_id": "central_corridor",
        "name": "Bus Terminal Link",
        "name_ru": "Автовокзальный узел",
        "latitude": 41.3136,
        "longitude": 69.2707,
        "coords": (41.3136, 69.2707),
        "traffic_light_id": "cluster_6",
        "signal_ids": ["cluster_6"],
    },
]

# Canonical Central Tashkent Corridor
CENTRAL_CORRIDOR: CorridorEntity = {
    "id": "central_corridor",
    "district_id": "central_tashkent",
    "name": "Central Tashkent Corridor",
    "name_ru": "Центральный коридор Ташкента",
    "bounds": {
        "southwest": [41.3080, 69.2550],
        "northeast": [41.3250, 69.2780],
        "polygon": [
            [41.3080, 69.2550],
            [41.3080, 69.2780],
            [41.3250, 69.2780],
            [41.3250, 69.2550],
        ],
    },
    "length_meters": 2450.0,
    "speed_limit_kmh": 60.0,
    "intersection_ids": [i["id"] for i in TASHKENT_INTERSECTIONS],
    "intersections": TASHKENT_INTERSECTIONS,
}

# Canonical Central Tashkent District
CENTRAL_DISTRICT: DistrictEntity = {
    "id": "central_tashkent",
    "city_id": "tashkent",
    "name": "Mirzo Ulugbek / Yunusabad District",
    "name_ru": "Мирзо-Улугбекский / Юнусабадский район",
    "bounds": {
        "southwest": [41.2950, 69.2400],
        "northeast": [41.3400, 69.2950],
    },
    "corridor_ids": ["central_corridor"],
    "corridors": [CENTRAL_CORRIDOR],
}

# Neighboring Districts (for cross-district readiness)
NEIGHBORING_DISTRICTS: List[DistrictEntity] = [
    {
        "id": "chilanzar_district",
        "city_id": "tashkent",
        "name": "Chilanzar District",
        "name_ru": "Чиланзарский район",
        "bounds": {"southwest": [41.2600, 69.1800], "northeast": [41.2950, 69.2400]},
        "corridor_ids": ["bunyodkor_avenue"],
        "corridors": [],
    },
    {
        "id": "yakkasaray_district",
        "city_id": "tashkent",
        "name": "Yakkasaray District",
        "name_ru": "Яккасарайский район",
        "bounds": {"southwest": [41.2700, 69.2400], "northeast": [41.3000, 69.2800]},
        "corridor_ids": ["shota_rustaveli_avenue"],
        "corridors": [],
    },
]

# Canonical Tashkent City Entity
TASHKENT_CITY: CityEntity = {
    "id": "tashkent",
    "name": "Tashkent",
    "name_ru": "Ташкент",
    "country": "Uzbekistan",
    "country_ru": "Узбекистан",
    "center": (41.2995, 69.2401),
    "bounds": {
        "southwest": [41.20, 69.10],
        "northeast": [41.40, 69.40],
    },
    "district_ids": ["central_tashkent", "chilanzar_district", "yakkasaray_district"],
    "districts": [CENTRAL_DISTRICT, *NEIGHBORING_DISTRICTS],
}


def get_spatial_hierarchy() -> CityEntity:
    """Returns the complete City -> District -> Corridor -> Intersection hierarchy."""
    return TASHKENT_CITY


def get_default_spatial_scope() -> SpatialScopeRef:
    """Returns the default spatial scope (Central Tashkent Corridor)."""
    return {
        "level": "corridor",
        "id": CENTRAL_CORRIDOR["id"],
        "name": CENTRAL_CORRIDOR["name"],
        "name_ru": CENTRAL_CORRIDOR["name_ru"],
        "city_name": TASHKENT_CITY["name"],
        "district_name": CENTRAL_DISTRICT["name"],
        "corridor_name": CENTRAL_CORRIDOR["name"],
    }


def get_cross_district_context() -> CrossDistrictContext:
    """Returns spatial context with primary and neighboring scopes for cross-district readiness."""
    primary = get_default_spatial_scope()
    neighbors: List[SpatialScopeRef] = [
        {
            "level": "district",
            "id": d["id"],
            "name": d["name"],
            "name_ru": d["name_ru"],
            "city_name": TASHKENT_CITY["name"],
            "district_name": d["name"],
            "corridor_name": "",
        }
        for d in NEIGHBORING_DISTRICTS
    ]
    return {
        "primary_scope": primary,
        "neighboring_scopes": neighbors,
        "spillover_effects": {
            "side_street_queue_spillover_risk": "low",
            "downstream_bottleneck_impact": "neutral",
            "cross_district_transit_continuity": "preserved",
        },
        "city_level_impact_indicator": 0.12,
    }


def find_intersection_by_signal_id(signal_id: str) -> Optional[IntersectionEntity]:
    """Lookup an intersection entity by its traffic light / cluster ID."""
    for item in TASHKENT_INTERSECTIONS:
        if item.get("traffic_light_id") == signal_id or signal_id in item.get("signal_ids", []):
            return item
    return None
