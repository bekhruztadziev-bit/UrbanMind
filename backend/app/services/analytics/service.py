from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


class ProductAnalyticsTracker:
    def __init__(self) -> None:
        self.experiments_run: int = 12
        self.scenarios_tested: int = 28
        self.policies_used: Dict[str, int] = {
            "balanced": 18,
            "flow": 12,
            "eco": 9,
            "custom": 5,
        }
        self.decision_reports_generated: int = 14
        self.report_exports: Dict[str, int] = {
            "json": 6,
            "csv": 8,
            "html_pdf": 11,
        }
        self.ai_analysis_requests: int = 15
        self.failed_experiments: int = 0
        self.experiment_durations_ms: List[float] = [1200.0, 1450.0, 1100.0, 1300.0]

    def record_event(self, event_type: str, details: Dict[str, Any] | None = None) -> None:
        d = details or {}
        if event_type == "experiment_run":
            self.experiments_run += 1
            dur = float(d.get("duration_ms", 1200.0))
            self.experiment_durations_ms.append(dur)
            scenario = str(d.get("scenario", "midday"))
            self.scenarios_tested += 1
            if d.get("failed"):
                self.failed_experiments += 1
        elif event_type == "policy_used":
            pol = str(d.get("policy", "balanced")).lower()
            self.policies_used[pol] = self.policies_used.get(pol, 0) + 1
        elif event_type == "report_generated":
            self.decision_reports_generated += 1
        elif event_type == "report_exported":
            fmt = str(d.get("format", "html_pdf")).lower()
            self.report_exports[fmt] = self.report_exports.get(fmt, 0) + 1
        elif event_type == "ai_request":
            self.ai_analysis_requests += 1

    def get_summary(self) -> Dict[str, Any]:
        avg_dur = (
            round(sum(self.experiment_durations_ms) / len(self.experiment_durations_ms), 1)
            if self.experiment_durations_ms
            else 0.0
        )
        return {
            "experiments_run": self.experiments_run,
            "scenarios_tested": self.scenarios_tested,
            "policies_used": self.policies_used,
            "decision_reports_generated": self.decision_reports_generated,
            "report_exports": self.report_exports,
            "ai_analysis_requests": self.ai_analysis_requests,
            "failed_experiments": self.failed_experiments,
            "average_experiment_duration_ms": avg_dur,
            "telemetry_timestamp": datetime.now(timezone.utc).isoformat(),
        }


_TRACKER = ProductAnalyticsTracker()


def record_analytics_event(event_type: str, details: Dict[str, Any] | None = None) -> None:
    _TRACKER.record_event(event_type, details)


def get_analytics_summary() -> Dict[str, Any]:
    return _TRACKER.get_summary()
