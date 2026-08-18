from __future__ import annotations

MAHALLA_BOUNDS = {
    "name": "Mahalla Center and surrounding corridor",
    "southwest": [41.3052, 69.2564],
    "northeast": [41.3276, 69.2804],
    "polygon": [
        [41.3052, 69.2564],
        [41.3052, 69.2804],
        [41.3276, 69.2804],
        [41.3276, 69.2564],
    ],
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

ROADS = [
    [[41.3098, 69.2620], [41.3238, 69.2620]],
    [[41.3098, 69.2680], [41.3238, 69.2680]],
    [[41.3098, 69.2730], [41.3238, 69.2730]],
    [[41.3165, 69.2598], [41.3165, 69.2758]],
    [[41.3190, 69.2598], [41.3190, 69.2758]],
    [[41.3135, 69.2598], [41.3135, 69.2758]],
    [[41.3212, 69.2598], [41.3212, 69.2758]],
]

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


def get_mahalla_data() -> dict:
    return {
        "name": MAHALLA_BOUNDS["name"],
        "bounds": MAHALLA_BOUNDS,
        "intersections": INTERSECTIONS,
        "roads": ROADS,
        "facilities": FACILITIES,
    }
