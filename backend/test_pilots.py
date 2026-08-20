from __future__ import annotations

import pytest
from app.services.pilots.service import (
    list_pilot_cases,
    get_pilot_case,
    create_pilot_case,
    update_pilot_case,
)


def test_list_pilot_cases():
    pilots = list_pilot_cases()
    assert len(pilots) >= 1
    tashkent_pilot = next((p for p in pilots if p["id"] == "PILOT-TASHKENT-CENTRAL-01"), None)
    assert tashkent_pilot is not None
    assert "Configured Demonstration Corridor" in tashkent_pilot["title"]
    assert tashkent_pilot["status"] == "DRAFT"
    assert tashkent_pilot["calibration_status"] == "UNCALIBRATED"


def test_get_pilot_case():
    pilot = get_pilot_case("PILOT-TASHKENT-CENTRAL-01")
    assert pilot is not None
    assert pilot["active_policy"] == "balanced"
    assert pilot["next_action"]["action_code"] == "FIELD_DETECTOR_VALIDATION"


def test_create_and_update_pilot_case():
    new_pilot = create_pilot_case({
        "title": "Chilanzar District Speed Harmonization",
        "title_ru": "Гармонизация скоростей в Чиланзарском районе",
        "status": "DRAFT",
        "active_policy": "eco",
    })

    assert new_pilot["id"].startswith("PILOT-")
    assert new_pilot["title"] == "Chilanzar District Speed Harmonization"
    assert new_pilot["status"] == "DRAFT"

    # Update
    updated = update_pilot_case(new_pilot["id"], {
        "status": "ANALYSIS",
        "problem_statement": "Elevated PM2.5 and stop-and-go acceleration on arterial avenue.",
    })

    assert updated is not None
    assert updated["status"] == "ANALYSIS"
    assert "PM2.5" in updated["problem_statement"]
