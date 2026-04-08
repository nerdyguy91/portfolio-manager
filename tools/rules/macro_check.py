"""
Macro rule evaluation.

Checks:
  - Yield curve inversion: US 2Y > US 10Y for 5 consecutive days
  - Commodity spike: PPIACO index +20% over 3 months
  - Bond yield shock: UK 10Y gilt +0.75% over 3 months
"""

from tools.db import get_macro_series

YIELD_CURVE_DAYS = 5
COMMODITY_SPIKE_THRESHOLD = 0.20      # 20%
BOND_SHOCK_THRESHOLD = 0.75           # 75 basis points
LOOKBACK_DAYS_3M = 65                 # ~3 calendar months of trading days


def check_yield_curve_inversion() -> dict | None:
    """
    Triggers if US 2Y yield > US 10Y yield for 5 consecutive most-recent days.
    """
    series_2y = get_macro_series("us_2y_yield", limit=YIELD_CURVE_DAYS + 5)
    series_10y = get_macro_series("us_10y_yield", limit=YIELD_CURVE_DAYS + 5)

    if len(series_2y) < YIELD_CURVE_DAYS or len(series_10y) < YIELD_CURVE_DAYS:
        return None

    # Build date-keyed dicts
    map_2y = {r.timestamp.date(): r.value for r in series_2y}
    map_10y = {r.timestamp.date(): r.value for r in series_10y}

    # Find dates present in both series, most recent first
    common_dates = sorted(set(map_2y) & set(map_10y), reverse=True)
    if len(common_dates) < YIELD_CURVE_DAYS:
        return None

    recent = common_dates[:YIELD_CURVE_DAYS]
    inverted = all(map_2y[d] > map_10y[d] for d in recent)

    if inverted:
        latest_2y = map_2y[recent[0]]
        latest_10y = map_10y[recent[0]]
        return {
            "type": "yield_curve_inversion",
            "severity": "High",
            "asset": "yield_curve",
            "message": (f"US yield curve has been inverted for {YIELD_CURVE_DAYS} consecutive days. "
                        f"2Y={latest_2y:.3f}%, 10Y={latest_10y:.3f}%."),
            "context": {"us_2y": latest_2y, "us_10y": latest_10y, "days_inverted": YIELD_CURVE_DAYS},
        }
    return None


def check_commodity_spike() -> dict | None:
    """
    Triggers if the commodity index has risen >20% over the last ~3 months.
    """
    series = get_macro_series("commodity_index", limit=LOOKBACK_DAYS_3M + 5)
    if len(series) < 2:
        return None

    latest = series[0].value
    oldest = series[-1].value
    if oldest == 0:
        return None

    change_pct = (latest - oldest) / oldest

    if change_pct > COMMODITY_SPIKE_THRESHOLD:
        return {
            "type": "commodity_spike",
            "severity": "High",
            "asset": "commodity_index",
            "message": (f"Commodity index has risen {change_pct:.1%} over the last 3 months "
                        f"({oldest:.2f} → {latest:.2f})."),
            "context": {"change_pct": change_pct, "start_value": oldest, "end_value": latest},
        }
    return None


def check_bond_yield_shock() -> dict | None:
    """
    Triggers if UK 10Y gilt yield has risen >0.75% over the last ~3 months.
    """
    series = get_macro_series("uk_10y_gilt", limit=LOOKBACK_DAYS_3M + 5)
    if len(series) < 2:
        return None

    latest = series[0].value
    oldest = series[-1].value
    change = latest - oldest  # absolute basis point change

    if change > BOND_SHOCK_THRESHOLD:
        return {
            "type": "bond_yield_shock",
            "severity": "High",
            "asset": "uk_10y_gilt",
            "message": (f"UK 10Y gilt yield has risen {change:.2f}% over the last 3 months "
                        f"({oldest:.3f}% → {latest:.3f}%)."),
            "context": {"change": change, "start_value": oldest, "end_value": latest},
        }
    return None


def run_all() -> list[dict]:
    alerts = []
    for check in [check_yield_curve_inversion, check_commodity_spike, check_bond_yield_shock]:
        result = check()
        if result:
            alerts.append(result)
    return alerts
