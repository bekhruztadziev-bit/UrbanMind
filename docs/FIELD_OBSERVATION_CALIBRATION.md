# Field Observation and Calibration Readiness

UrbanMind is a simulation-supported decision system. It remains `UNCALIBRATED` unless genuine field observations are imported, mapped to the versioned SUMO network, and evaluated.

## Observation import

CSV and JSON imports use these fields: `dataset_id`, `purpose`, `campaign_id`, `simulation_campaign_id`, `timestamp`, `measurement_window_id`, `intersection_id`, `approach_id`, `movement`, `interval_minutes`, `vehicle_count`, `vehicle_class`, `source`, `quality`, and `notes`.

`purpose` is exactly `CALIBRATION` or `VALIDATION_HOLDOUT`. Imports return row-level diagnostics; invalid rows are not silently accepted. CSV templates intentionally contain only headers, never example traffic counts.
Only `HIGH_PRECISION` and `STANDARD_TELEMETRY` quality flags are admissible for traffic calibration; proxy and synthetic records are rejected.

## Movement mapping

The authoritative mapping registry connects city, district, corridor, intersection, approach, and movement to SUMO incoming/outgoing edges, lanes, link, and signal. A mapping must be verified against the versioned SUMO network before being enabled. The shipped registry currently has no enabled records because the repository does not contain survey-approved mappings from its named corridor intersections to the opaque SUMO network identifiers. Therefore an unmapped observation is rejected and cannot affect calibration status.

## Comparison and provenance

Calibration compares one observed movement count with one `SIMULATED` SUMO movement count having the same mapping ID, passenger class, observation interval, simulation campaign, measurement window, network configuration hash, and mapping version. It calculates MAE, RMSE, MAPE, mean bias error, Pearson correlation, and GEH only for comparable flow quantities. The acceptance values in code are UrbanMind configured criteria; they are not claimed as universal standards.

## Lifecycle and holdout

The lifecycle is `UNCALIBRATED → PARTIALLY_CALIBRATED → CALIBRATED → VALIDATED`. A holdout must have a different dataset ID, campaign ID, content fingerprint, and non-overlapping observation windows, plus `VALIDATION_HOLDOUT` purpose and a completed independent comparison. Calibration records cannot be reused or relabelled to achieve `VALIDATED`.

## Current limitation

There are no imported field observations and no enabled production mappings. The TraCI movement counter is wired into completed simulations, but it exports no production counts until jointly verified mappings are enabled. The next work is field collection plus a jointly verified mapping/detector configuration.
