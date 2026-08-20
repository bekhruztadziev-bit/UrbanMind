# SUMO Movement Mapping Verification

## Network discovery record

The checked-in `osm.net.xml.gz` is a SUMO 1.27.1 network with SHA-256 `1a3820654600dcc64c6cf40c58a2189b492440160eb318f495aeff0a1430be7c`. Its projection is UTM zone 42; the original coordinate boundary is `69.253255,41.291426,69.323230,41.343381`. It contains 51 TLS programs, 72 signal junctions, and 18,936 network connections. Route input defines one `veh_passenger` type with SUMO `passenger` class and no configured emission-class declaration.

For example, TLS/junction `1853907420` is at SUMO coordinates `1188.56,1950.90` and has incoming lanes beginning `636093172#2_0`, `636093172#2_1`, and `636093172#2_2`. These identifiers are network facts, not a verified link to any named UrbanMind product intersection.

No repository evidence associates the product labels such as `intersection_1` or `Main Square` with a particular SUMO junction, edge, lane, or TLS link. Consequently there are currently zero `UNVERIFIED`, `NETWORK_VERIFIED`, `FIELD_VERIFIED`, or `ENABLED` production mapping records. No production mapping is eligible for calibration.

## Mapping approval workflow

Mapping records are immutable dataclasses. They carry network/configuration hashes, mapping version, edge/lane/TLS details, geometry, verification method, verifier, and time. A record becomes calibration-eligible only when `enabled`, `verification_status=ENABLED`, network/configuration hashes, and verifier metadata are all present. A changed geometry or configuration requires a new mapping ID/version.

`GET /api/mappings/{mapping_id}/audit` checks a record against the current network and returns candidate connection evidence. It can return only `NOT_APPROVED_AUTOMATICALLY`; human field verification remains required.

## TraCI movement counter

During the measurement phase, `MovementCounter` remembers each active vehicle's prior measured edge. It records one count only when the next measured edge is the mapping's verified outgoing edge after the verified incoming edge. It does not use edge totals, route demand, throughput, or policy scores. The counter starts after warm-up and de-duplicates `(mapping_id, vehicle_id)`.

Exports are `SIMULATED` and carry simulation ID, seed, SUMO version, network and route hashes, mapping/version, interval boundaries, class breakdown, and method `VEHICLE_MOVEMENT_TRANSITION_COUNT`. The present SUMO route model has only `veh_passenger → passenger_car`; it cannot support a class-specific calibration claim for buses, trucks, or motorcycles.

## Comparison boundary

`POST /api/calibration/evaluate` accepts a completed `simulation_id`, never caller-supplied counts. It retrieves the recorded SUMO movement export and rejects absent, unmatched, non-`SIMULATED`, wrong-interval, wrong-network-version, or non-eligible mapping evidence. It compares exact same-interval movement counts only.

The system remains `UNCALIBRATED` until genuine field observations and enabled field-verified mappings exist.
