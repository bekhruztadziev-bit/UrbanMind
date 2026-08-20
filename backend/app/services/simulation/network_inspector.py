"""Read-only inspection of the versioned SUMO network for mapping review."""
from __future__ import annotations

import gzip
import hashlib
from pathlib import Path
from typing import Any, Dict, List
from xml.etree import ElementTree as ET


SCENARIO_DIR = Path(__file__).resolve().parents[3] / "sim" / "mahalla-scenario"
NETWORK_PATH = SCENARIO_DIR / "osm.net.xml.gz"
ROUTE_PATH = SCENARIO_DIR / "osm.passenger.trips.xml"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_network_identity() -> Dict[str, str]:
    return {
        "network_file": NETWORK_PATH.name,
        "network_sha256": _sha256(NETWORK_PATH),
        "route_file": ROUTE_PATH.name,
        "route_sha256": _sha256(ROUTE_PATH),
        "network_version": f"sha256:{_sha256(NETWORK_PATH)}",
    }


def inspect_network() -> Dict[str, Any]:
    """Return candidate SUMO entities for human mapping verification only."""
    root = ET.fromstring(gzip.decompress(NETWORK_PATH.read_bytes()))
    location = next((item.attrib for item in root.findall("location")), {})
    junctions = []
    for item in root.findall("junction"):
        if item.attrib.get("type") in {"traffic_light", "traffic_light_right_on_red"}:
            junctions.append({
                "junction_id": item.attrib.get("id"), "x": item.attrib.get("x"), "y": item.attrib.get("y"),
                "incoming_lanes": item.attrib.get("incLanes", "").split(),
                "internal_lanes": item.attrib.get("intLanes", "").split(),
            })
    edge_junction = {
        edge.attrib.get("id"): edge.attrib.get("from")
        for edge in root.findall("edge")
        if edge.attrib.get("id")
    }
    connections = []
    for item in root.findall("connection"):
        incoming_edge = item.attrib.get("from")
        outgoing_edge = item.attrib.get("to")
        incoming_lane = f"{incoming_edge}_{item.attrib.get('fromLane')}" if incoming_edge is not None else None
        outgoing_lane = f"{outgoing_edge}_{item.attrib.get('toLane')}" if outgoing_edge is not None else None
        via_lane = item.attrib.get("via")
        via_edge = via_lane.rsplit("_", 1)[0] if via_lane and "_" in via_lane else via_lane
        connections.append({
            "incoming_edge_id": incoming_edge, "outgoing_edge_id": outgoing_edge,
            "incoming_lane_id": incoming_lane, "outgoing_lane_id": outgoing_lane,
            "incoming_lane_index": item.attrib.get("fromLane"), "outgoing_lane_index": item.attrib.get("toLane"),
            "via_lane_id": via_lane, "via_edge_id": via_edge,
            "junction_id": edge_junction.get(via_edge) or edge_junction.get(outgoing_edge),
            "tls_id": item.attrib.get("tl"), "tls_link_index": item.attrib.get("linkIndex"),
            "direction": item.attrib.get("dir"), "is_signalized": bool(item.attrib.get("tl")),
        })
    route_root = ET.parse(ROUTE_PATH).getroot()
    vehicle_types = [{"id": item.attrib.get("id"), "vclass": item.attrib.get("vClass"), "emission_class": item.attrib.get("emissionClass")} for item in route_root.findall("vType")]
    return {
        **get_network_identity(), "location": location, "signal_junctions": junctions,
        "tls_ids": [item.attrib.get("id") for item in root.findall("tlLogic")],
        "connections": connections, "tls_connections": [c for c in connections if c["is_signalized"]], "vehicle_types": vehicle_types,
        "verification_notice": "Candidate entities are not approved field mappings. Human field verification is required before enablement.",
    }


def verify_mapping_topology(mapping: Any) -> Dict[str, Any]:
    """Verify one exact SUMO connection tuple; never infer an approval."""
    data = inspect_network()
    expected = getattr(mapping, "configuration_hash", "")
    candidates = [item for item in data["connections"] if item["incoming_edge_id"] == mapping.incoming_edge and item["outgoing_edge_id"] == mapping.outgoing_edge]

    def exact(item: Dict[str, Any]) -> bool:
        incoming_ok = not mapping.incoming_lane_ids or item["incoming_lane_id"] in mapping.incoming_lane_ids
        outgoing_ok = not mapping.outgoing_lane_ids or item["outgoing_lane_id"] in mapping.outgoing_lane_ids
        junction_ok = not mapping.junction_id or item["junction_id"] == mapping.junction_id
        direction_ok = not mapping.direction or item["direction"] == mapping.direction
        signal_ok = mapping.is_signalized is not None and item["is_signalized"] == mapping.is_signalized
        via_ok = item["via_lane_id"] == mapping.via_lane_id
        if mapping.is_signalized:
            tls_ok = item["tls_id"] == mapping.tls_id and str(item["tls_link_index"]) == str(mapping.tls_link_index)
        else:
            tls_ok = item["tls_id"] is None and mapping.tls_id is None and mapping.tls_link_index is None
        return incoming_ok and outgoing_ok and junction_ok and direction_ok and signal_ok and via_ok and tls_ok

    exact_matches = [item for item in candidates if exact(item)]
    return {
        "mapping_id": mapping.mapping_id,
        "network_version_matches": getattr(mapping, "network_version", "") == data["network_version"],
        "network_hash_matches": expected == data["network_sha256"],
        "candidate_connections": candidates,
        "exact_connections": exact_matches,
        "is_exact_match": bool(exact_matches) and getattr(mapping, "network_version", "") == data["network_version"] and expected == data["network_sha256"],
        "verification_status": mapping.verification_status,
        "approval": "NOT_APPROVED_AUTOMATICALLY",
    }


def inspect_mapping_candidate(mapping: Any) -> Dict[str, Any]:
    """Compatibility inspection output for human review; it never approves a record."""
    verified = verify_mapping_topology(mapping)
    return {
        **verified,
        "edge_connection_exists": bool(verified["candidate_connections"]),
        "incoming_lane_matches": bool(verified["exact_connections"]),
        "tls_matches": bool(verified["exact_connections"]),
        "tls_link_index_matches": bool(verified["exact_connections"]),
    }
