from typing import Any, TypedDict, List, Optional, Dict, Literal


class MetricValue(TypedDict, total=False):
    value: float
    unit: str
    source: str          # "traci_simulation" | "waqi_api" | "formula_derived" | "calibrated_fallback"
    provenance: str      # "DIRECT" | "SIMULATED" | "OBSERVED" | "ESTIMATED" | "FALLBACK"
    confidence: str      # "high" | "medium" | "low"
    is_simulated: bool


class InterventionDefinition(TypedDict, total=False):
    type: str
    category: str
    label: str
    seconds: int
    traffic_light_id: str
    phase_index: int
    evaluation_mode: str  # 'SIMULATED' or 'HEURISTIC'


class SimulationRequest(TypedDict, total=False):
    steps: int
    warmup_steps: int
    measurement_steps: int
    scenario: str
    intervention: Optional[Dict[str, Any]]
    traffic_multiplier: float
    seed: Optional[int]


class RawSimulationResult(TypedDict, total=False):
    steps: int
    warmup_steps: int
    measurement_steps: int
    scenario: str
    simulation_time_seconds: float
    traffic_light_count: int
    traffic_light_ids: List[str]
    total_speed: float
    total_waiting: float
    samples: int
    max_vehicle_count: int
    mean_completed_vehicle_time_loss_seconds: Optional[float]
    completed_vehicle_count: int
    mean_active_vehicle_time_loss_seconds: Optional[float]
    active_vehicle_count: int
    mean_completed_vehicle_waiting_seconds: Optional[float]
    mean_active_vehicle_waiting_seconds: Optional[float]
    departure_based_vehicle_delay: Optional[float]
    # Detailed traffic flow physics
    total_travel_time_seconds: float
    average_travel_time_seconds: float
    mean_queue_length_meters: float
    total_stops: int
    stops_per_vehicle: float
    throughput_vehicles_per_hour: float
    total_vehicles_departed: int
    total_vehicles_arrived: int
    # SUMO emission model outputs (accumulated over measurement window)
    total_co2_mg: float    # mg, from traci.vehicle.getCO2Emission
    total_nox_mg: float    # mg, from traci.vehicle.getNOxEmission
    total_pmx_mg: float    # mg, from traci.vehicle.getPMxEmission
    total_fuel_mg: float   # mg, from traci.vehicle.getFuelConsumption
    is_fallback: bool


class SimulationMetrics(TypedDict, total=False):
    steps: int
    warmup_steps: int
    measurement_steps: int
    scenario: str
    simulation_time_seconds: float
    traffic_light_count: int
    traffic_light_ids: List[str]
    max_vehicle_count: int
    average_speed_kmh: float
    average_waiting_seconds: float
    mean_completed_vehicle_time_loss_seconds: Optional[float]
    completed_vehicle_count: int
    mean_active_vehicle_time_loss_seconds: Optional[float]
    active_vehicle_count: int
    mean_completed_vehicle_waiting_seconds: Optional[float]
    mean_active_vehicle_waiting_seconds: Optional[float]
    # Physics & Flow metrics
    average_travel_time_seconds: float
    mean_queue_length_meters: float
    stops_per_vehicle: float
    throughput_vehicles_per_hour: float
    total_vehicles_departed: int
    total_vehicles_arrived: int
    # Environmental metrics
    co2_kg: float               # ESTIMATED — legacy formula
    nox_g: float                # ESTIMATED — legacy formula
    noise_db: float             # ESTIMATED — legacy formula
    pedestrian_delay_seconds: float
    accessibility_score: float
    departure_based_vehicle_delay: Optional[float]
    # SUMO emission model outputs (SIMULATED provenance)
    sumo_co2_kg: float          # SIMULATED — from SUMO HBEFA emission model
    sumo_nox_g: float           # SIMULATED — from SUMO HBEFA emission model
    sumo_pmx_mg: float          # SIMULATED — from SUMO HBEFA emission model
    sumo_fuel_ml: float         # SIMULATED — from SUMO HBEFA emission model
    is_fallback: bool
    structured_metrics: Optional[Dict[str, MetricValue]]


class CandidateDelta(TypedDict, total=False):
    average_speed_kmh: float
    average_waiting_seconds: float
    average_travel_time_seconds: Optional[float]
    mean_queue_length_meters: Optional[float]
    stops_per_vehicle: Optional[float]
    throughput_vehicles_per_hour: Optional[float]
    mean_completed_vehicle_time_loss_seconds: Optional[float]
    mean_active_vehicle_time_loss_seconds: Optional[float]
    mean_completed_vehicle_waiting_seconds: Optional[float]
    mean_active_vehicle_waiting_seconds: Optional[float]
    max_vehicle_count: int
    co2_kg: float
    nox_g: float
    noise_db: float
    pedestrian_delay_seconds: float
    accessibility_score: float
    departure_based_vehicle_delay: Optional[float]
    sumo_co2_kg: Optional[float]
    sumo_nox_g: Optional[float]
    # Percentage improvements (positive means improvement)
    delay_improvement_pct: Optional[float]
    travel_time_improvement_pct: Optional[float]
    queue_improvement_pct: Optional[float]
    stops_improvement_pct: Optional[float]
    throughput_improvement_pct: Optional[float]
    emissions_improvement_pct: Optional[float]


class CandidateResult(TypedDict, total=False):
    id: str
    label: str
    label_en: str
    label_ru: str
    category: str
    category_label: str
    type: str
    description: str
    summary: str
    evaluation_mode: str
    intervention: InterventionDefinition
    metrics: SimulationMetrics
    delta: CandidateDelta
    score: float
    selected_reason: str
    selected_reason_ru: str


class OptimizationResult(TypedDict, total=False):
    scenario: str
    baseline: SimulationMetrics
    candidates: List[CandidateResult]
    ranked_candidates: List[CandidateResult]
    best_candidate: CandidateResult
    ai: Any
    insights: Any
    product_positioning: Any


class MetricDeltaItem(TypedDict):
    absolute: float
    percentage: Optional[float]


class MetricDelta(TypedDict, total=False):
    average_speed_kmh: MetricDeltaItem
    average_waiting_seconds: MetricDeltaItem
    average_travel_time_seconds: Optional[MetricDeltaItem]
    mean_queue_length_meters: Optional[MetricDeltaItem]
    stops_per_vehicle: Optional[MetricDeltaItem]
    throughput_vehicles_per_hour: Optional[MetricDeltaItem]
    mean_completed_vehicle_time_loss_seconds: Optional[MetricDeltaItem]
    mean_active_vehicle_time_loss_seconds: Optional[MetricDeltaItem]
    mean_completed_vehicle_waiting_seconds: Optional[MetricDeltaItem]
    mean_active_vehicle_waiting_seconds: Optional[MetricDeltaItem]
    max_vehicle_count: MetricDeltaItem
    co2_kg: MetricDeltaItem
    nox_g: MetricDeltaItem
    noise_db: MetricDeltaItem
    pedestrian_delay_seconds: MetricDeltaItem
    accessibility_score: MetricDeltaItem
    departure_based_vehicle_delay: Optional[MetricDeltaItem]
    sumo_co2_kg: Optional[MetricDeltaItem]


class ScenarioRequest(TypedDict, total=False):
    traffic_multiplier: float
    duration: int
    intervention_id: Optional[str]


MetricProvenance = Literal["DIRECT", "DERIVED", "ESTIMATED", "SIMULATED", "OBSERVED", "FALLBACK"]


class ScenarioComparisonResult(TypedDict):
    scenario_metadata: ScenarioRequest
    normal_baseline: Optional[SimulationMetrics]
    control: SimulationMetrics
    scenario: SimulationMetrics
    deltas: MetricDelta
    intervention: Optional[InterventionDefinition]
    metric_provenance: Dict[str, MetricProvenance]
    evaluation_mode: Optional[str]


# ---------------------------------------------------------------------------
# Experiment Runner models
# ---------------------------------------------------------------------------

class ExperimentRequest(TypedDict, total=False):
    name: str
    traffic_levels: List[float]
    intervention_ids: List[str]
    duration: int
    warmup_steps: int
    measurement_steps: int
    simulation_profile: Optional[str]


class ExperimentCondition(TypedDict, total=False):
    condition_id: str
    traffic_multiplier: float
    intervention_id: Optional[str]
    intervention_label: str
    evaluation_mode: str          # 'SIMULATED' | 'HEURISTIC' | 'CONTROL'
    control_metrics: Optional[SimulationMetrics]
    scenario_metrics: Optional[SimulationMetrics]
    metric_deltas: Optional[MetricDelta]
    metric_provenance: Dict[str, MetricProvenance]
    status: str                   # 'COMPLETED' | 'FAILED' | 'SKIPPED'
    error: Optional[str]


class ExperimentSummary(TypedDict):
    total: int
    completed: int
    failed: int
    skipped: int
    status: str                   # 'COMPLETED' | 'PARTIALLY_COMPLETED' | 'FAILED'


class ExperimentMetadata(TypedDict, total=False):
    urbanmind_version: str
    scenario_network: str
    random_seed: Optional[str]
    sumo_version: Optional[str]
    effective_criterion: str
    simulation_profile: Optional[str]


class ExperimentResult(TypedDict):
    experiment_id: str
    schema_version: int
    name: str
    created_at: str
    duration: int
    traffic_levels: List[float]
    intervention_ids: List[str]
    conditions: List[ExperimentCondition]
    summary: ExperimentSummary
    metadata: ExperimentMetadata
    metric_provenance: Dict[str, MetricProvenance]
