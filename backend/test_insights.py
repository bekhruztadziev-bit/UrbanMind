from app.services.insights import build_neighborhood_summary


def test_build_neighborhood_summary_mentions_category_and_name():
    summary = build_neighborhood_summary(
        {
            'average_speed_kmh': 18.5,
            'average_waiting_seconds': 28.0,
            'max_vehicle_count': 44,
            'traffic_light_count': 6,
        },
        {
            'label': 'Extend green light by 10s',
            'summary': 'Gives the school corridor more discharge capacity.'
        },
    )

    assert summary['product_name'] == 'MahallaMind'
    assert summary['category'] == 'Neighborhood Mobility Intelligence'
    assert 'school' in summary['focus'].lower()
    assert isinstance(summary['signals'], list)
    assert summary['signals']
