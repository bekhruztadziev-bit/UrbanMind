import math
import pytest
from app.services.simulation.statistics import (
    get_t_critical,
    compute_sample_statistics,
    compute_geh,
    evaluate_geh_batch,
    compute_relative_delta_pct,
)


def test_t_critical_exact_values():
    # n = 3 -> df = 2 -> t = 4.303
    t_df2 = get_t_critical(df=2)
    assert round(t_df2, 3) == 4.303

    # n = 2 -> df = 1 -> t = 12.706
    t_df1 = get_t_critical(df=1)
    assert round(t_df1, 3) == 12.706

    # n = 4 -> df = 3 -> t = 3.182
    t_df3 = get_t_critical(df=3)
    assert round(t_df3, 3) == 3.182

    # n = 6 -> df = 5 -> t = 2.571
    t_df5 = get_t_critical(df=5)
    assert round(t_df5, 3) == 2.571

    # Large n -> converges towards 1.960
    t_df120 = get_t_critical(df=120)
    assert 1.95 <= t_df120 <= 2.00


def test_sample_statistics_n3():
    # 3 seeds for green wave delay: [16.2, 17.5, 16.8]
    data = [16.2, 17.5, 16.8]
    stats = compute_sample_statistics(data)

    assert stats["sample_count"] == 3
    assert stats["degrees_of_freedom"] == 2
    assert stats["t_critical"] == 4.303
    assert stats["mean"] == pytest.approx(16.83, 0.05)
    
    # Verify standard deviation uses Bessel's correction (n - 1)
    mean_val = sum(data) / 3
    expected_var = sum((x - mean_val) ** 2 for x in data) / 2
    expected_std = math.sqrt(expected_var)
    assert stats["std_dev"] == pytest.approx(round(expected_std, 2), 0.05)

    # Margin of error = t * (s / sqrt(3))
    expected_se = expected_std / math.sqrt(3)
    expected_me = 4.303 * expected_se
    assert stats["margin_of_error"] == pytest.approx(round(expected_me, 2), 0.05)
    assert stats["ci_95_low"] == pytest.approx(max(0.0, round(mean_val - expected_me, 2)), 0.05)
    assert stats["ci_95_high"] == pytest.approx(round(mean_val + expected_me, 2), 0.05)


def test_sample_statistics_zero_variance():
    data = [20.0, 20.0, 20.0]
    stats = compute_sample_statistics(data)
    assert stats["sample_count"] == 3
    assert stats["std_dev"] == 0.0
    assert stats["margin_of_error"] == 0.0
    assert stats["ci_95_low"] == 20.0
    assert stats["ci_95_high"] == 20.0


def test_sample_statistics_missing_values():
    data = [15.0, None, 18.0, float("nan"), 16.5]
    stats = compute_sample_statistics(data)
    assert stats["sample_count"] == 3
    assert stats["mean"] == pytest.approx(16.5, 0.05)


def test_sample_statistics_single_value():
    data = [24.5]
    stats = compute_sample_statistics(data)
    assert stats["sample_count"] == 1
    assert stats["mean"] == 24.5
    assert stats["std_dev"] == 0.0
    assert stats["ci_95_low"] == 24.5
    assert stats["ci_95_high"] == 24.5


def test_geh_statistic_calculation():
    # GEH formula: sqrt( 2 * (M - C)^2 / (M + C) )
    # Example: Modeled = 420, Observed = 400
    # 2 * 20^2 / 820 = 800 / 820 = 0.9756 -> sqrt = 0.988 -> 0.99
    geh = compute_geh(simulated_flow=420, observed_flow=400)
    assert geh == pytest.approx(0.99, 0.05)

    # Identical flow -> GEH = 0.0
    assert compute_geh(500, 500) == 0.0

    # Zero flows -> GEH = 0.0
    assert compute_geh(0, 0) == 0.0


def test_geh_batch_webtag_standards():
    # 5 link flows: 4 have GEH < 5 (80%), 1 has GEH > 5
    pairs = [
        (400, 410),  # GEH ~ 0.50 (< 5)
        (650, 620),  # GEH ~ 1.19 (< 5)
        (320, 310),  # GEH ~ 0.56 (< 5)
        (800, 780),  # GEH ~ 0.71 (< 5)
        (1000, 700), # GEH ~ 10.29 (>= 5)
    ]
    res = evaluate_geh_batch(pairs, threshold=5.0, required_pass_rate=85.0)
    assert res["sample_count"] == 5
    assert res["pct_under_5"] == 80.0
    assert res["is_webtag_compliant"] is False  # 80% < 85%

    # 6th link with GEH < 5 -> 5/6 = 83.3%, 7th link with GEH < 5 -> 6/7 = 85.7% (Compliant)
    pairs_pass = pairs + [(500, 490), (300, 295)]
    res_pass = evaluate_geh_batch(pairs_pass, threshold=5.0, required_pass_rate=85.0)
    assert res_pass["pct_under_5"] >= 85.0
    assert res_pass["is_webtag_compliant"] is True
