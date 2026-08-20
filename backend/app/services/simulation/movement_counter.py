"""Authoritative TraCI movement-transition counter for verified mappings."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from app.services.calibration.mappings import MovementMapping
from app.services.simulation.network_inspector import get_network_identity


SUMO_TYPE_TO_FIELD_CLASS = {"veh_passenger": "passenger_car"}
_MOVEMENT_COUNT_RUNS: Dict[str, List[Dict[str, Any]]] = {}


def store_movement_counts(simulation_id: str, counts: List[Dict[str, Any]]) -> None:
    _MOVEMENT_COUNT_RUNS[simulation_id] = counts


def get_movement_counts(simulation_id: str) -> List[Dict[str, Any]] | None:
    return _MOVEMENT_COUNT_RUNS.get(simulation_id)


class MovementCounter:
    """Counts one vehicle only when its sampled edge transition matches a mapping."""

    def __init__(self, mappings: Iterable[MovementMapping], simulation_id: str, seed: Any, measurement_start: float, measurement_steps: int):
        self.mappings = tuple(mapping for mapping in mappings if mapping.calibration_eligible)
        self.simulation_id = simulation_id
        self.seed = seed
        self.measurement_start = measurement_start
        self.measurement_steps = measurement_steps
        # mapping/vehicle state is reset after the vehicle leaves a completed
        # movement, permitting a legitimate repeated traversal on loop routes.
        self._state: Dict[tuple[str, str], str] = {}
        self._counts: Counter[str] = Counter()
        self._classes: Dict[str, Counter[str]] = {mapping.mapping_id: Counter() for mapping in self.mappings}

    def observe_step(self, traci: Any) -> None:
        """Observe post-step edge state; warm-up is excluded by caller construction."""
        current_ids = set(traci.vehicle.getIDList())
        for vehicle_id in current_ids:
            try:
                current_edge = traci.vehicle.getRoadID(vehicle_id)
                current_lane = traci.vehicle.getLaneID(vehicle_id)
                type_id = traci.vehicle.getTypeID(vehicle_id)
            except Exception:
                continue
            for mapping in self.mappings:
                count_key = (mapping.mapping_id, vehicle_id)
                state = self._state.get(count_key, "IDLE")
                incoming_lane_ok = not mapping.incoming_lane_ids or current_lane in mapping.incoming_lane_ids
                outgoing_lane_ok = not mapping.outgoing_lane_ids or current_lane in mapping.outgoing_lane_ids
                on_incoming = current_edge == mapping.incoming_edge and incoming_lane_ok
                on_via = mapping.via_lane_id is not None and current_lane == mapping.via_lane_id
                on_outgoing = current_edge == mapping.outgoing_edge and outgoing_lane_ok

                if state == "IDLE" and on_incoming:
                    self._state[count_key] = "INCOMING"
                elif state == "INCOMING":
                    if mapping.via_lane_id is not None:
                        if on_via:
                            self._state[count_key] = "VIA"
                        elif not on_incoming:
                            # No inferred edge jump may stand in for a known via lane.
                            self._state.pop(count_key, None)
                    elif on_outgoing:
                        self._state[count_key] = "COMPLETED"
                        self._counts[mapping.mapping_id] += 1
                        self._classes[mapping.mapping_id][SUMO_TYPE_TO_FIELD_CLASS.get(type_id, "unclassified")] += 1
                    elif not on_incoming:
                        self._state.pop(count_key, None)
                elif state == "VIA":
                    if on_outgoing:
                        self._state[count_key] = "COMPLETED"
                        self._counts[mapping.mapping_id] += 1
                        self._classes[mapping.mapping_id][SUMO_TYPE_TO_FIELD_CLASS.get(type_id, "unclassified")] += 1
                    elif not on_via:
                        self._state.pop(count_key, None)
                elif state == "COMPLETED" and not on_outgoing:
                    self._state.pop(count_key, None)
        # A disappearance, teleport, or removal discards incomplete state. A
        # later vehicle appearance must prove the full chain again.
        for key in [key for key in self._state if key[1] not in current_ids]:
            self._state.pop(key, None)

    def export(self, measurement_end: float, sumo_version: Any) -> List[Dict[str, Any]]:
        identity = get_network_identity()
        interval_seconds = measurement_end - self.measurement_start
        interval_minutes = interval_seconds / 60.0
        return [{
            "mapping_id": mapping.mapping_id,
            "mapping_version": mapping.mapping_version,
            "source": "TRACI_MOVEMENT_COUNTER", "provenance": "SIMULATED",
            "network_version": identity["network_version"], "network_configuration_hash": identity["network_sha256"],
            "route_configuration_hash": identity["route_sha256"], "simulation_id": self.simulation_id,
            "seed": self.seed, "sumo_version": str(sumo_version),
            "measurement_start_seconds": self.measurement_start, "measurement_end_seconds": measurement_end,
            "measurement_window_id": f"{self.simulation_id}:{self.measurement_start:.3f}:{measurement_end:.3f}",
            "interval_minutes": interval_minutes, "measurement_steps": self.measurement_steps,
            "simulation_vehicle_class": "passenger_car",
            "warmup_excluded": True, "intersection_id": mapping.intersection_id,
            "approach_id": mapping.approach_id, "movement": mapping.movement,
            "incoming_lane_ids": list(mapping.incoming_lane_ids), "outgoing_lane_ids": list(mapping.outgoing_lane_ids),
            "via_lane_id": mapping.via_lane_id, "direction": mapping.direction,
            "junction_id": mapping.junction_id, "tls_id": mapping.tls_id, "tls_link_index": mapping.tls_link_index,
            "vehicle_count": self._counts[mapping.mapping_id], "vehicle_classes": dict(self._classes[mapping.mapping_id]),
            "quality": "SIMULATION_DIRECT_TRANSITION", "method": "VEHICLE_MOVEMENT_TRANSITION_COUNT",
            "created_at": datetime.now(timezone.utc).isoformat(),
        } for mapping in self.mappings]
