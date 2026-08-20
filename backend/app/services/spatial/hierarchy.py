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

# Product demonstration labels. They are not field-verified intersections.
TASHKENT_INTERSECTIONS: List[IntersectionEntity] = [
    {
        "id": "demo_signal_group_a",
        "corridor_id": "central_corridor",
        "name": "Signal Group A (demonstration)",
        "name_ru": "Группа сигналов A (демонстрация)",
        "latitude": 41.3168,
        "longitude": 69.2666,
        "coords": (41.3168, 69.2666),
        "signal_ids": [],
    },
    {
        "id": "demo_signal_group_b",
        "corridor_id": "central_corridor",
        "name": "Signal Group B (demonstration)",
        "name_ru": "Группа сигналов B (демонстрация)",
        "latitude": 41.3182,
        "longitude": 69.2684,
        "coords": (41.3182, 69.2684),
        "signal_ids": [],
    },
    {
        "id": "demo_signal_group_c",
        "corridor_id": "central_corridor",
        "name": "Signal Group C (demonstration)",
        "name_ru": "Группа сигналов C (демонстрация)",
        "latitude": 41.3157,
        "longitude": 69.2692,
        "coords": (41.3157, 69.2692),
        "signal_ids": [],
    },
    {
        "id": "demo_signal_group_d",
        "corridor_id": "central_corridor",
        "name": "Signal Group D (demonstration)",
        "name_ru": "Группа сигналов D (демонстрация)",
        "latitude": 41.3149,
        "longitude": 69.2638,
        "coords": (41.3149, 69.2638),
        "signal_ids": [],
    },
    {
        "id": "demo_signal_group_e",
        "corridor_id": "central_corridor",
        "name": "Signal Group E (demonstration)",
        "name_ru": "Группа сигналов E (демонстрация)",
        "latitude": 41.3199,
        "longitude": 69.2718,
        "coords": (41.3199, 69.2718),
        "signal_ids": [],
    },
    {
        "id": "demo_signal_group_f",
        "corridor_id": "central_corridor",
        "name": "Signal Group F (demonstration)",
        "name_ru": "Группа сигналов F (демонстрация)",
        "latitude": 41.3136,
        "longitude": 69.2707,
        "coords": (41.3136, 69.2707),
        "signal_ids": [],
    },
]

# Configured simulation extent; no municipal district or named corridor claim.
CENTRAL_CORRIDOR: CorridorEntity = {
    "id": "central_corridor",
    "district_id": "central_tashkent",
    "name": "Configured Demonstration Corridor",
    "name_ru": "Настроенный демонстрационный коридор",
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
    "intersection_ids": [i["id"] for i in TASHKENT_INTERSECTIONS],
    "intersections": TASHKENT_INTERSECTIONS,
}

# District assignment is intentionally unavailable pending field verification.
CENTRAL_DISTRICT: DistrictEntity = {
    "id": "central_tashkent",
    "city_id": "tashkent",
    "name": "Unverified demonstration district",
    "name_ru": "Неверифицированный демонстрационный район",
    "bounds": {
        "southwest": [41.2950, 69.2400],
        "northeast": [41.3400, 69.2950],
    },
    "corridor_ids": ["central_corridor"],
    "corridors": [CENTRAL_CORRIDOR],
}

NEIGHBORING_DISTRICTS: List[DistrictEntity] = []

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
    "district_ids": ["central_tashkent"],
    "districts": [CENTRAL_DISTRICT, *NEIGHBORING_DISTRICTS],
}


def get_spatial_hierarchy() -> CityEntity:
    """Returns the complete City -> District -> Corridor -> Intersection hierarchy."""
    return TASHKENT_CITY


def get_default_spatial_scope() -> SpatialScopeRef:
    """Return a clearly labelled configured demonstration scope."""
    return {
        "level": "corridor",
        "id": CENTRAL_CORRIDOR["id"],
        "name": CENTRAL_CORRIDOR["name"],
        "name_ru": CENTRAL_CORRIDOR["name_ru"],
        "city_name": TASHKENT_CITY["name"],
        "district_name": CENTRAL_DISTRICT["name"],
        "corridor_name": CENTRAL_CORRIDOR["name"],
        "spatial_provenance": "PRODUCT_DEMO_LABEL",
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
        "spillover_effects": {"status": "NOT_EVALUATED"},
        "city_level_impact_indicator": None,
    }


def find_intersection_by_signal_id(signal_id: str) -> Optional[IntersectionEntity]:
    """Lookup an intersection entity by its traffic light / cluster ID."""
    for item in TASHKENT_INTERSECTIONS:
        if item.get("traffic_light_id") == signal_id or signal_id in item.get("signal_ids", []):
            return item
    return None
