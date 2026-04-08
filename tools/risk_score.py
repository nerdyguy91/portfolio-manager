"""
Portfolio risk score calculator.

Produces a 0–100 score from the set of active (unsuppressed) alerts.
Weighting is fixed for v1.
"""

from tools.db import get_active_alerts

# Weights per (alert_type, severity)
WEIGHTS: dict[tuple, int] = {
    ("dividend_cover", "Critical"):    25,
    ("dividend_cover", "Medium"):      15,
    ("cadi_break", "Critical"):        20,
    ("cadi_break", "Medium"):          10,
    ("yield_spike", "High"):           15,
    ("market_cap_low", "Medium"):       5,
    ("ftse_drawdown", "Critical"):     25,
    ("ftse_drawdown", "High"):         15,
    ("ftse_drawdown", "Medium"):       10,
    ("ftse_drawdown", "Low"):           5,
    ("vix_spike", "High"):             15,
    ("yield_curve_inversion", "High"): 10,
    ("commodity_spike", "High"):       10,
    ("bond_yield_shock", "High"):      10,
}

MAX_MACRO_CONTRIBUTION = 30  # cap macro signals at 30 points total


def compute_risk_score(active_alerts: list = None) -> int:
    """
    Compute portfolio risk score (0–100).
    If active_alerts is None, fetches from DB.
    """
    if active_alerts is None:
        active_alerts = get_active_alerts()

    macro_types = {"yield_curve_inversion", "commodity_spike", "bond_yield_shock"}
    score = 0
    macro_score = 0

    for alert in active_alerts:
        key = (alert.type, alert.severity)
        weight = WEIGHTS.get(key, 0)
        if alert.type in macro_types:
            macro_score += weight
        else:
            score += weight

    score += min(macro_score, MAX_MACRO_CONTRIBUTION)
    return min(score, 100)


if __name__ == "__main__":
    from tools.db import init_db
    init_db()
    score = compute_risk_score()
    print(f"Current portfolio risk score: {score}/100")
