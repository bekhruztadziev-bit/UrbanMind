from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict


class IntersectionEntity(TypedDict, total=False):
    id: str
    corridor_id: str
    name: str
    name_ru: str
    latitude: float
    longitude: float
    coords: Tuple[float, float]
    traffic_light_id: str
    signal_ids: List[str]


class CorridorEntity(TypedDict, total=False):
    id: str
    district_id: str
    name: str
    name_ru: str
    bounds: Dict[str, Any]
    length_meters: float
    speed_limit_kmh: float
    intersection_ids: List[str]
    intersections: List[IntersectionEntity]


class DistrictEntity(TypedDict, total=False):
    id: str
    city_id: str
    name: str
    name_ru: str
    bounds: Dict[str, Any]
    corridor_ids: List[str]
    corridors: List[CorridorEntity]


class CityEntity(TypedDict, total=False):
    id: str
    name: str
    name_ru: str
    country: str
    country_ru: str
    center: Tuple[float, float]
    bounds: Dict[str, Any]
    district_ids: List[str]
    districts: List[DistrictEntity]


class SpatialScopeRef(TypedDict, total=False):
    level: Literal["city", "district", "corridor", "intersection"]
    id: str
    name: str
    name_ru: str
    city_name: str
    district_name: str
    corridor_name: str


class CrossDistrictContext(TypedDict, total=False):
    primary_scope: SpatialScopeRef
    neighboring_scopes: List[SpatialScopeRef]
    spillover_effects: Dict[str, Any]
    city_level_impact_indicator: float
