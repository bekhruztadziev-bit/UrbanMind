from app.services.calibration.mappings import MovementMapping
from app.services.simulation.movement_counter import MovementCounter
from app.services.simulation.network_inspector import get_network_identity


class FakeVehicles:
    def __init__(self):
        self.edges = {}
        self.lanes = {}
        self.types = {}

    def getIDList(self):
        return list(self.edges)

    def getRoadID(self, vehicle_id):
        return self.edges[vehicle_id]

    def getTypeID(self, vehicle_id):
        return self.types.get(vehicle_id, "veh_passenger")

    def getLaneID(self, vehicle_id):
        return self.lanes[vehicle_id]


class FakeTraci:
    def __init__(self):
        self.vehicle = FakeVehicles()


def _mapping(**changes):
    identity = get_network_identity()
    values = dict(
        mapping_id="test-map", city_id="test", district_id="test", corridor_id="test",
        intersection_id="test_ix", intersection_name="Test", approach_id="north", approach_name="North",
        movement="through", incoming_edge="edge-a", outgoing_edge="edge-b", lane_ids=("edge-a_0",),
        signal_id=None, enabled=True, notes="Test-only mapping", network_version=identity["network_version"],
        configuration_hash=identity["network_sha256"], incoming_lane_ids=("edge-a_0",),
        verification_status="ENABLED", verification_method="TEST_FIXTURE", verified_at="2026-08-20T00:00:00Z", verified_by="test-suite",
    )
    values.update(changes)
    return MovementMapping(**values)


def test_counter_counts_only_one_matching_transition_and_preserves_provenance():
    traci = FakeTraci()
    counter = MovementCounter([_mapping()], "sim-test", 42, 100.0, 60)
    traci.vehicle.edges = {"veh-1": "edge-a", "veh-2": "edge-a"}
    traci.vehicle.lanes = {"veh-1": "edge-a_0", "veh-2": "edge-a_0"}
    counter.observe_step(traci)
    traci.vehicle.edges = {"veh-1": "edge-b", "veh-2": "other-edge"}
    traci.vehicle.lanes = {"veh-1": "edge-b_0", "veh-2": "other-edge_0"}
    counter.observe_step(traci)
    counter.observe_step(traci)  # A stationary vehicle must not be counted twice.
    exported = counter.export(160.0, ("SUMO 1.27.1", "1.27.1"))
    assert exported[0]["vehicle_count"] == 1
    assert exported[0]["vehicle_classes"] == {"passenger_car": 1}
    assert exported[0]["provenance"] == "SIMULATED"
    assert exported[0]["seed"] == 42
    assert exported[0]["warmup_excluded"] is True


def test_counter_does_not_count_a_transition_that_began_before_measurement():
    traci = FakeTraci()
    counter = MovementCounter([_mapping()], "sim-test", 7, 100.0, 60)
    # The counter is intentionally constructed after warm-up; it has no
    # inbound transition evidence for this vehicle, so this is excluded.
    traci.vehicle.edges = {"veh-1": "edge-b"}
    traci.vehicle.lanes = {"veh-1": "edge-b_0"}
    counter.observe_step(traci)
    assert counter.export(160.0, "SUMO")[0]["vehicle_count"] == 0


def test_counter_requires_the_verified_internal_via_lane_when_mapping_defines_one():
    traci = FakeTraci()
    mapping = _mapping(via_lane_id=":junction_0_0", outgoing_lane_ids=("edge-b_0",))
    counter = MovementCounter([mapping], "sim-test", 7, 100.0, 60)
    traci.vehicle.edges = {"veh-1": "edge-a"}
    traci.vehicle.lanes = {"veh-1": "edge-a_0"}
    counter.observe_step(traci)
    # An edge jump without the verified via lane is not evidence of a turn.
    traci.vehicle.edges = {"veh-1": "edge-b"}
    traci.vehicle.lanes = {"veh-1": "edge-b_0"}
    counter.observe_step(traci)
    assert counter.export(160.0, "SUMO")[0]["vehicle_count"] == 0

    # A complete incoming -> via -> outgoing traversal is counted once.
    traci.vehicle.edges = {"veh-2": "edge-a"}
    traci.vehicle.lanes = {"veh-2": "edge-a_0"}
    counter.observe_step(traci)
    traci.vehicle.edges = {"veh-2": ":junction_0"}
    traci.vehicle.lanes = {"veh-2": ":junction_0_0"}
    counter.observe_step(traci)
    traci.vehicle.edges = {"veh-2": "edge-b"}
    traci.vehicle.lanes = {"veh-2": "edge-b_0"}
    counter.observe_step(traci)
    assert counter.export(160.0, "SUMO")[0]["vehicle_count"] == 1
