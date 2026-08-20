"""Authoritative field-observation to SUMO movement mapping registry.

Records are deliberately curated rather than inferred from OSM or display-map
geometry.  The checked-in SUMO network has opaque identifiers and currently
has no field-survey-approved correspondence to the product's named
intersections, so the production registry starts empty.  Adding a record is a
data-governance action: its SUMO edge/lane/link identifiers must be verified
against the versioned network before it is enabled.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Dict, Iterable, List, Literal, Optional, Tuple


MappingVerificationStatus = Literal["UNVERIFIED", "NETWORK_VERIFIED", "FIELD_VERIFIED", "ENABLED"]
_ALLOWED_TRANSITIONS = {
    "UNVERIFIED": {"NETWORK_VERIFIED"},
    "NETWORK_VERIFIED": {"FIELD_VERIFIED"},
    "FIELD_VERIFIED": {"ENABLED"},
    "ENABLED": set(),
}


@dataclass(frozen=True)
class MovementMapping:
    mapping_id: str
    city_id: str
    district_id: str
    corridor_id: str
    intersection_id: str
    intersection_name: str
    approach_id: str
    approach_name: str
    movement: str
    incoming_edge: str
    outgoing_edge: str
    lane_ids: Tuple[str, ...]
    signal_id: Optional[str]
    enabled: bool
    notes: str
    # Evidence/version fields. Defaults preserve deserialization of legacy
    # drafts; legacy records are never calibration-eligible.
    network_version: str = ""
    configuration_hash: str = ""
    mapping_version: str = "v1"
    incoming_lane_ids: Tuple[str, ...] = ()
    outgoing_lane_ids: Tuple[str, ...] = ()
    junction_id: Optional[str] = None
    tls_id: Optional[str] = None
    tls_link_index: Optional[int] = None
    # Exact SUMO connection identity. A via lane is required for the normal
    # signalized connections in the configured network. None explicitly means
    # a direct, unsignalized connection; it never means "unknown".
    via_lane_id: Optional[str] = None
    direction: Optional[str] = None
    is_signalized: Optional[bool] = None
    geometry: Optional[Tuple[float, float]] = None
    verification_status: str = "UNVERIFIED"
    verification_method: str = ""
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None

    def serialize(self) -> Dict[str, object]:
        value = asdict(self)
        value["lane_ids"] = list(self.lane_ids)
        value["incoming_lane_ids"] = list(self.incoming_lane_ids)
        value["outgoing_lane_ids"] = list(self.outgoing_lane_ids)
        value["city"] = self.city_id
        value["district"] = self.district_id
        value["intersection_label"] = self.intersection_name
        value["approach_label"] = self.approach_name
        value["incoming_edge_id"] = self.incoming_edge
        value["outgoing_edge_id"] = self.outgoing_edge
        return value

    @property
    def calibration_eligible(self) -> bool:
        return bool(
            self.enabled and self.verification_status == "ENABLED" and self.network_version
            and self.configuration_hash and self.verified_at and self.verified_by
        )

    @property
    def is_test_fixture(self) -> bool:
        return self.verification_method.startswith("TEST_FIXTURE")


def transition_mapping_status(
    mapping: MovementMapping,
    target_status: MappingVerificationStatus,
    *,
    verified_at: str,
    verified_by: str,
    verification_method: str,
    allow_test_fixture: bool = False,
) -> MovementMapping:
    """Return a new mapping after one permitted governance transition.

    Production mappings cannot skip from a draft directly to ENABLED. The
    final transition also verifies the current network topology and identity.
    Tests may opt in explicitly through a TEST_FIXTURE record; that exception
    cannot occur in the checked-in production registry.
    """
    current = mapping.verification_status
    if target_status not in _ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid mapping verification transition: {current} -> {target_status}")
    if target_status == "ENABLED" and not (allow_test_fixture and mapping.is_test_fixture):
        from app.services.simulation.network_inspector import verify_mapping_topology
        verification = verify_mapping_topology(mapping)
        if not verification["is_exact_match"]:
            raise ValueError("Mapping cannot be ENABLED until current network topology is exactly verified.")
    return replace(
        mapping,
        verification_status=target_status,
        enabled=target_status == "ENABLED",
        verified_at=verified_at,
        verified_by=verified_by,
        verification_method=verification_method,
    )


# Do not add guessed records here.  This is intentionally empty until the
# network version and the real-world approach/movement are signed off.
CANONICAL_MOVEMENT_MAPPINGS: Tuple[MovementMapping, ...] = ()


class MovementMappingRegistry:
    def __init__(self, records: Iterable[MovementMapping] = CANONICAL_MOVEMENT_MAPPINGS):
        self._records = tuple(records)
        self._by_key: Dict[Tuple[str, str, str], MovementMapping] = {}
        self._by_id: Dict[str, MovementMapping] = {}
        for record in self._records:
            if record.verification_status not in _ALLOWED_TRANSITIONS:
                raise ValueError(f"Unknown mapping verification status: {record.verification_status}")
            if record.enabled != (record.verification_status == "ENABLED"):
                raise ValueError("Mapping enabled flag must exactly match ENABLED verification status.")
            key = (record.intersection_id, record.approach_id, record.movement)
            if key in self._by_key or record.mapping_id in self._by_id:
                raise ValueError(f"Duplicate movement mapping: {record.mapping_id}")
            self._by_key[key] = record
            self._by_id[record.mapping_id] = record

    def lookup(self, intersection_id: str, approach_id: str, movement: str) -> Optional[MovementMapping]:
        record = self._by_key.get((intersection_id, approach_id, movement))
        if not record or not record.calibration_eligible:
            return None
        # A caller must not be able to bypass the topology verification that
        # eligible_records() applies.  This is intentionally repeated here
        # because field-import validation uses lookup() directly.
        if record.is_test_fixture:
            return record
        from app.services.simulation.network_inspector import verify_mapping_topology
        return record if verify_mapping_topology(record)["is_exact_match"] else None

    def by_id(self, mapping_id: str) -> Optional[MovementMapping]:
        return self._by_id.get(mapping_id)

    def eligible_records(self) -> Tuple[MovementMapping, ...]:
        eligible: List[MovementMapping] = []
        for record in self._records:
            if not record.calibration_eligible:
                continue
            if record.is_test_fixture:
                eligible.append(record)
                continue
            from app.services.simulation.network_inspector import verify_mapping_topology
            if verify_mapping_topology(record)["is_exact_match"]:
                eligible.append(record)
        return tuple(eligible)

    def by_intersection(self, intersection_id: str) -> List[Dict[str, object]]:
        return [r.serialize() for r in self._records if r.intersection_id == intersection_id]

    def all(self) -> List[Dict[str, object]]:
        return [r.serialize() for r in self._records]

    def coverage(self) -> Dict[str, object]:
        # "enabled" coverage means usable by imports, not merely carrying an
        # ENABLED flag in a draft registry file.
        enabled = list(self.eligible_records())
        intersections = sorted({r.intersection_id for r in enabled})
        return {
            "configured_movement_count": len(self._records),
            "enabled_movement_count": len(enabled),
            "verification_status_counts": {status: sum(1 for r in self._records if r.verification_status == status) for status in ("UNVERIFIED", "NETWORK_VERIFIED", "FIELD_VERIFIED", "ENABLED")},
            "mapped_intersection_ids": intersections,
            "coverage_status": "UNAVAILABLE" if not enabled else "PARTIAL",
            "provenance": "ASSUMPTION_FREE_REGISTRY",
            "limitation": (
                "No verified field-intersection to SUMO movement mappings are configured yet. "
                "Unmapped field observations are rejected and cannot calibrate the model."
                if not enabled else "Only enabled, version-verified mappings may be used for calibration."
            ),
        }


_REGISTRY = MovementMappingRegistry()


def get_mapping_registry() -> MovementMappingRegistry:
    return _REGISTRY


def get_observation_template() -> Dict[str, object]:
    return {
        "required_columns": [
            "dataset_id", "purpose", "campaign_id", "simulation_campaign_id", "timestamp", "measurement_window_id", "intersection_id", "approach_id",
            "movement", "interval_minutes", "vehicle_count", "vehicle_class", "source",
            "quality", "notes",
        ],
        "csv_header": (
            "dataset_id,purpose,campaign_id,simulation_campaign_id,timestamp,measurement_window_id,intersection_id,approach_id,movement,"
            "interval_minutes,vehicle_count,vehicle_class,source,quality,notes"
        ),
        "allowed_purposes": ["CALIBRATION", "VALIDATION_HOLDOUT"],
        "allowed_movements": ["through", "left", "right", "u_turn"],
        "allowed_vehicle_classes": ["passenger_car"],
        "allowed_quality_flags": ["HIGH_PRECISION", "STANDARD_TELEMETRY"],
        "note": "Passenger-only SUMO currently supports only passenger_car comparison. The template intentionally contains no sample observations. Obtain verified mapping IDs, a pre-fit campaign allocation, and an explicit SUMO measurement-window ID before collection.",
        "mapping_coverage": _REGISTRY.coverage(),
    }
