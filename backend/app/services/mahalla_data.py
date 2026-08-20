from __future__ import annotations

MAHALLA_BOUNDS = {
    "name": "Configured Demonstration Corridor",
    "spatial_provenance": "PRODUCT_DEMO_LABEL",
    "southwest": [41.3080, 69.2550],
    "northeast": [41.3250, 69.2780],
    "polygon": [
        [41.3080, 69.2550],
        [41.3080, 69.2780],
        [41.3250, 69.2780],
        [41.3250, 69.2550],
    ],
}

# Broader Tashkent urban context — for expanded map view
TASHKENT_CONTEXT = {
    "name": "Tashkent",
    "center": [41.2995, 69.2401],
    "display_bounds": {
        "southwest": [41.24, 69.12],
        "northeast": [41.38, 69.38],
    },
    "simulation_region": MAHALLA_BOUNDS,
}

INTERSECTIONS = [
    {
        "id": "demo_signal_group_a",
        "name": "Signal Group A (demonstration)",
        "coords": [41.3168, 69.2666],
        "traffic_light_ids": [], "spatial_provenance": "PRODUCT_DEMO_LABEL",
    },
    {
        "id": "demo_signal_group_b",
        "name": "Signal Group B (demonstration)",
        "coords": [41.3182, 69.2684],
        "traffic_light_ids": [], "spatial_provenance": "PRODUCT_DEMO_LABEL",
    },
    {
        "id": "demo_signal_group_c",
        "name": "Signal Group C (demonstration)",
        "coords": [41.3157, 69.2692],
        "traffic_light_ids": [], "spatial_provenance": "PRODUCT_DEMO_LABEL",
    },
    {
        "id": "demo_signal_group_d",
        "name": "Signal Group D (demonstration)",
        "coords": [41.3149, 69.2638],
        "traffic_light_ids": [], "spatial_provenance": "PRODUCT_DEMO_LABEL",
    },
    {
        "id": "demo_signal_group_e",
        "name": "Signal Group E (demonstration)",
        "coords": [41.3199, 69.2718],
        "traffic_light_ids": [], "spatial_provenance": "PRODUCT_DEMO_LABEL",
    },
    {
        "id": "demo_signal_group_f",
        "name": "Signal Group F (demonstration)",
        "coords": [41.3136, 69.2707],
        "traffic_light_ids": [], "spatial_provenance": "PRODUCT_DEMO_LABEL",
    },
]

ROADS = []

# No facility points are presented in the conference build until they are
# verified against the simulation network and field scope.
FACILITIES = []

# Known Tashkent environmental monitoring stations
# Source: Uzhydromet (monitoring.meteo.uz)
MONITORING_STATIONS = [
    {"id": "uzhydromet_chilanzar", "name": "Chilanzar", "coords": [41.2856, 69.2128], "source": "Uzhydromet"},
    {"id": "uzhydromet_center", "name": "Amir Temur", "coords": [41.3111, 69.2797], "source": "Uzhydromet"},
    {"id": "uzhydromet_sergeli", "name": "Sergeli", "coords": [41.2275, 69.2199], "source": "Uzhydromet"},
    {"id": "uzhydromet_olmazor", "name": "Olmazor", "coords": [41.3377, 69.2150], "source": "Uzhydromet"},
    {"id": "uzhydromet_yakkasaray", "name": "Yakkasaray", "coords": [41.2887, 69.2864], "source": "Uzhydromet"},
]


def get_mahalla_data() -> dict:
    return {
        "name": MAHALLA_BOUNDS["name"],
        "bounds": MAHALLA_BOUNDS,
        "intersections": INTERSECTIONS,
        "roads": ROADS,
        "facilities": FACILITIES,
        "urban_context": TASHKENT_CONTEXT,
        "monitoring_stations": MONITORING_STATIONS,
    }
