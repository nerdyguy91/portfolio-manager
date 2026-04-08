"""
Market stress rule evaluation.

Checks:
  - FTSE 100 drawdown vs 90-day rolling high (4 levels)
  - VIX > 30
"""

from tools.db import get_market_data

DRAWDOWN_WINDOW = 90  # days

DRAWDOWN_LEVELS = [
    (0.20, "Critical", 4),
    (0.15, "High",     3),
    (0.10, "Medium",   2),
    (0.05, "Low",      1),
]

VIX_THRESHOLD = 30.0


def compute_drawdown(window_days: int = DRAWDOWN_WINDOW) -> dict | None:
    """
    Computes FTSE 100 drawdown vs the rolling high over the last `window_days` days.
    Returns {"drawdown": float, "current": float, "high": float} or None if no data.
    """
    rows = get_market_data("^FTSE", limit=window_days)
    if not rows:
        return None
    prices = [r.price for r in rows]
    current = prices[0]           # most recent (rows ordered DESC)
    high = max(prices)
    drawdown = (high - current) / high if high > 0 else 0.0
    return {"drawdown": drawdown, "current": current, "high": high}


def check_drawdown() -> dict | None:
    result = compute_drawdown()
    if result is None:
        return None

    drawdown = result["drawdown"]
    for threshold, severity, level in DRAWDOWN_LEVELS:
        if drawdown >= threshold:
            return {
                "type": "ftse_drawdown",
                "severity": severity,
                "asset": "^FTSE",
                "message": (f"FTSE 100 is down {drawdown:.1%} from its 90-day high "
                            f"({result['high']:.2f} → {result['current']:.2f}). "
                            f"Drawdown Level {level}."),
                "context": {**result, "level": level},
            }
    return None


def check_vix() -> dict | None:
    rows = get_market_data("^VIX", limit=1)
    if not rows:
        return None
    vix = rows[0].price
    if vix > VIX_THRESHOLD:
        return {
            "type": "vix_spike",
            "severity": "High",
            "asset": "^VIX",
            "message": f"VIX is at {vix:.2f}, above the stress threshold of {VIX_THRESHOLD}.",
            "context": {"vix": vix},
        }
    return None


def run_all() -> list[dict]:
    alerts = []
    for check in [check_drawdown, check_vix]:
        result = check()
        if result:
            alerts.append(result)
    return alerts
