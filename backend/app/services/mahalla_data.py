from __future__ import annotations

MAHALLA_BOUNDS = {
    "name": "Tashkent Central Corridor",
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
        "id": "intersection_1",
        "name": "Main Square",
        "coords": [41.3168, 69.2666],
        "traffic_light_ids": ["cluster_1"],
    },
    {
        "id": "intersection_2",
        "name": "School Junction",
        "coords": [41.3182, 69.2684],
        "traffic_light_ids": ["cluster_2"],
    },
    {
        "id": "intersection_3",
        "name": "Clinic Roundabout",
        "coords": [41.3157, 69.2692],
        "traffic_light_ids": ["cluster_3"],
    },
    {
        "id": "intersection_4",
        "name": "Market Edge",
        "coords": [41.3149, 69.2638],
        "traffic_light_ids": ["cluster_4"],
    },
    {
        "id": "intersection_5",
        "name": "North Residential Corridor",
        "coords": [41.3199, 69.2718],
        "traffic_light_ids": ["cluster_5"],
    },
    {
        "id": "intersection_6",
        "name": "Bus Terminal Link",
        "coords": [41.3136, 69.2707],
        "traffic_light_ids": ["cluster_6"],
    },
]

ROADS = []

FACILITIES = [
    {"id": "school_1", "type": "school", "name": "District School", "coords": [41.3186, 69.2698]},
    {"id": "clinic_1", "type": "clinic", "name": "Community Clinic", "coords": [41.3154, 69.2676]},
    {"id": "kindergarten_1", "type": "kindergarten", "name": "Kindergarten #4", "coords": [41.3171, 69.2648]},
    {"id": "bus_stop_1", "type": "bus_stop", "name": "Bus Stop East", "coords": [41.3191, 69.2661]},
    {"id": "park_1", "type": "park", "name": "Park", "coords": [41.3138, 69.2702]},
    {"id": "facility_1", "type": "administrative", "name": "Mahalla Office", "coords": [41.3147, 69.2641]},
    {"id": "facility_2", "type": "public", "name": "Community Center", "coords": [41.3198, 69.2709]},
    {"id": "market_1", "type": "market", "name": "Market Square", "coords": [41.3128, 69.2645]},
    {"id": "mosque_1", "type": "religious", "name": "Mosque Lane", "coords": [41.3213, 69.2727]},
]

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
