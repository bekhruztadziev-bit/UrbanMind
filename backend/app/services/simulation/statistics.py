from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

# Exact Student-t critical values for two-tailed alpha=0.05 (95% Confidence Interval)
# Degrees of Freedom (df = n - 1)
STUDENT_T_CRITICAL_TABLE_95: Dict[int, float] = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
    40: 2.021,
    50: 2.009,
    60: 2.000,
    80: 1.990,
    100: 1.984,
    120: 1.980,
}


def get_t_critical(df: int, alpha: float = 0.05) -> float:
    """
    Returns the two-tailed critical value t_{1 - alpha/2, df} for Student-t distribution.
    Uses scipy.stats if installed, falling back to the exact lookup table / asymptotic formula.
    For large degrees of freedom (df > 120), smoothly converges to normal critical value (1.960 for alpha=0.05).
    """
    if df < 1:
        return 1.960

    try:
        from scipy import stats  # type: ignore
        return float(stats.t.ppf(1.0 - alpha / 2.0, df))
    except Exception:
        pass

    if df in STUDENT_T_CRITICAL_TABLE_95:
        return STUDENT_T_CRITICAL_TABLE_95[df]

    # Interpolate or asymptotic expansion for df > 30
    if df > 120:
        return 1.960 + (2.35 / df)
    
    # Nearest key search in table
    table_keys = sorted(STUDENT_T_CRITICAL_TABLE_95.keys())
    for i in range(len(table_keys) - 1):
        k1, k2 = table_keys[i], table_keys[i + 1]
        if k1 <= df <= k2:
            t1, t2 = STUDENT_T_CRITICAL_TABLE_95[k1], STUDENT_T_CRITICAL_TABLE_95[k2]
            frac = (df - k1) / (k2 - k1)
            return round(t1 + frac * (t2 - t1), 3)

    return 1.960


def compute_sample_statistics(
    values: List[Optional[float]],
    alpha: float = 0.05,
    allow_negative_ci: bool = False
) -> Dict[str, Any]:
    """
    Computes mathematically rigorous sample statistics using Bessel's correction (n - 1)
    and exact Student-t 95% Confidence Intervals.

    Args:
        values: List of empirical sample observations (missing/None values filtered).
        alpha: Significance level (default 0.05 for 95% CI).
        allow_negative_ci: If False, clips lower CI bound at 0.0 for non-negative metrics (delay, emissions).

    Returns:
        Dictionary containing sample_count, mean, variance, std_dev, standard_error,
        df, t_critical, margin_of_error, ci_95_low, ci_95_high, min, max, ci_method.
    """
    clean_vals = [float(v) for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    n = len(clean_vals)

    if n == 0:
        return {
            "sample_count": 0,
            "mean": None,
            "variance": None,
            "std_dev": None,
            "standard_error": None,
            "degrees_of_freedom": 0,
            "t_critical": None,
            "margin_of_error": None,
            "ci_95_low": None,
            "ci_95_high": None,
            "min": None,
            "max": None,
            "ci_method": "Insufficient data (n=0)",
        }

    mean_val = sum(clean_vals) / n

    if n == 1:
        return {
            "sample_count": 1,
            "mean": round(mean_val, 2),
            "variance": 0.0,
            "std_dev": 0.0,
            "standard_error": 0.0,
            "degrees_of_freedom": 0,
            "t_critical": None,
            "margin_of_error": 0.0,
            "ci_95_low": round(mean_val, 2),
            "ci_95_high": round(mean_val, 2),
            "min": round(clean_vals[0], 2),
            "max": round(clean_vals[0], 2),
            "ci_method": "Single seed observation (no stochastic variance estimate)",
        }

    # Sample variance with Bessel's correction (n - 1)
    df = n - 1
    sum_sq_diff = sum((x - mean_val) ** 2 for x in clean_vals)
    variance = sum_sq_diff / df
    std_dev = math.sqrt(variance)
    standard_error = std_dev / math.sqrt(n)

    # Zero variance case (all seeds returned identical metrics)
    if std_dev == 0.0:
        return {
            "sample_count": n,
            "mean": round(mean_val, 2),
            "variance": 0.0,
            "std_dev": 0.0,
            "standard_error": 0.0,
            "degrees_of_freedom": df,
            "t_critical": get_t_critical(df, alpha),
            "margin_of_error": 0.0,
            "ci_95_low": round(mean_val, 2),
            "ci_95_high": round(mean_val, 2),
            "min": round(min(clean_vals), 2),
            "max": round(max(clean_vals), 2),
            "ci_method": f"Student-t 95% CI (df={df}, zero variance across seeds)",
        }

    t_crit = get_t_critical(df, alpha)
    margin_of_error = t_crit * standard_error

    ci_low = mean_val - margin_of_error
    if not allow_negative_ci:
        ci_low = max(0.0, ci_low)
    ci_high = mean_val + margin_of_error

    return {
        "sample_count": n,
        "mean": round(mean_val, 2),
        "variance": round(variance, 4),
        "std_dev": round(std_dev, 2),
        "standard_error": round(standard_error, 3),
        "degrees_of_freedom": df,
        "t_critical": round(t_crit, 3),
        "margin_of_error": round(margin_of_error, 2),
        "ci_95_low": round(ci_low, 2),
        "ci_95_high": round(ci_high, 2),
        "min": round(min(clean_vals), 2),
        "max": round(max(clean_vals), 2),
        "ci_method": f"Student-t 95% CI (df={df}, t={t_crit:.3f}, Bessel-corrected sample s)",
    }


def compute_geh(simulated_flow: float, observed_flow: float) -> float:
    """
    Computes the Geoffrey E. Havers (GEH) statistic for traffic flow comparisons.
    Formula: GEH = sqrt( 2 * (M - C)^2 / (M + C) )
    where M = modeled flow (veh/h) and C = observed count (veh/h).
    """
    m = float(simulated_flow)
    c = float(observed_flow)
    if m < 0.0 or c < 0.0:
        raise ValueError("GEH requires non-negative modeled and observed flows.")

    if m + c == 0.0:
        return 0.0

    numerator = 2.0 * ((m - c) ** 2)
    denominator = m + c
    return round(math.sqrt(numerator / denominator), 2)


def evaluate_geh_batch(
    comparisons: List[Tuple[float, float]],
    threshold: float = 5.0,
    required_pass_rate: float = 85.0
) -> Dict[str, Any]:
    """Evaluate configured UrbanMind GEH acceptance criteria.

    Defaults are informed by traffic-assignment guidance; they are project
    methodology settings, not a universal legal or scientific threshold.
    """
    if not comparisons:
        return {
            "sample_count": 0,
            "mean_geh": None,
            "max_geh": None,
            "pct_under_5": 0.0,
            "threshold": threshold,
            "required_pass_rate": required_pass_rate,
            "is_criteria_met": False,
            # Compatibility alias; it is not a claim of formal WebTAG
            # certification. New callers must use is_criteria_met.
            "is_webtag_compliant": False,
            "notes_en": "No flow comparison pairs provided for GEH evaluation.",
            "notes_ru": "Нет пар сопоставления потоков для расчета статистики GEH.",
        }

    geh_values = [compute_geh(m, c) for m, c in comparisons]
    n = len(geh_values)
    under_threshold_count = sum(1 for g in geh_values if g < threshold)
    pct_under = round((under_threshold_count / n) * 100.0, 1)
    is_compliant = pct_under >= required_pass_rate

    return {
        "sample_count": n,
        "geh_values": geh_values,
        "mean_geh": round(sum(geh_values) / n, 2),
        "max_geh": round(max(geh_values), 2),
        "pct_under_5": pct_under,
        "threshold": threshold,
        "required_pass_rate": required_pass_rate,
        "is_criteria_met": is_compliant,
        "is_webtag_compliant": is_compliant,
        "notes_en": f"GEH < {threshold} for {pct_under}% of movements ({under_threshold_count}/{n}). UrbanMind configured criterion (informed by traffic-assignment guidance, >= {required_pass_rate}%): {'PASS' if is_compliant else 'FAIL'}.",
        "notes_ru": f"GEH < {threshold} для {pct_under}% направлений ({under_threshold_count}/{n}). Настроенный критерий UrbanMind (основан на рекомендациях по транспортному моделированию, >= {required_pass_rate}%): {'СОБЛЮДЕН' if is_compliant else 'НЕ СОБЛЮДЕН'}.",
    }


def compute_relative_delta_pct(baseline_val: float, candidate_val: float) -> float:
    """
    Computes percentage improvement where positive indicates improvement.
    For delay / emissions (lower is better): (base - cand) / base * 100.
    """
    if baseline_val == 0.0:
        return 0.0
    return round(((baseline_val - candidate_val) / baseline_val) * 100.0, 1)
