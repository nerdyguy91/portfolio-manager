"""
Alert lifecycle management.

Responsibilities:
  - Deduplication: suppress identical (type, asset) alerts within 24h
  - Escalation: allow through if severity has increased
  - Action generation: rule-map alert_type + severity → recommended actions
  - Routing: return severity bucket for downstream (explanation / notification)
"""

from datetime import timedelta
from tools.db import (
    create_alert, suppress_alert, get_recent_alert, create_action,
    severity_increased, now, Alert
)

# --- Action rule map ---
# (alert_type, severity) → list of (action_type, description, direction)
ACTION_MAP: dict[tuple, list[dict]] = {
    ("dividend_cover", "Critical"): [
        {"action_type": "reduce_exposure", "description": "Consider reducing position size to limit dividend income risk.", "direction": "decrease"},
        {"action_type": "investigate", "description": "Review company earnings reports for EPS trend and guidance.", "direction": None},
    ],
    ("dividend_cover", "Medium"): [
        {"action_type": "monitor", "description": "Monitor dividend cover over the next two reporting periods.", "direction": None},
    ],
    ("cadi_break", "Critical"): [
        {"action_type": "reduce_exposure", "description": "Dividend cut detected — review position and consider reducing.", "direction": "decrease"},
        {"action_type": "investigate", "description": "Investigate reason for dividend cut: structural or temporary?", "direction": None},
    ],
    ("cadi_break", "Medium"): [
        {"action_type": "monitor", "description": "Dividend growth stalled — monitor for further deterioration.", "direction": None},
    ],
    ("yield_spike", "High"): [
        {"action_type": "investigate", "description": "Yield spike may signal market concern about dividend sustainability. Investigate.", "direction": None},
        {"action_type": "reduce_exposure", "description": "Consider trimming position until sustainability is confirmed.", "direction": "decrease"},
    ],
    ("market_cap_low", "Medium"): [
        {"action_type": "monitor", "description": "Company has fallen below £300M market cap. Liquidity risk increases.", "direction": None},
    ],
    ("ftse_drawdown", "Critical"): [
        {"action_type": "rotate", "description": "Rotate into defensive sectors (utilities, consumer staples, healthcare).", "direction": "rotate"},
        {"action_type": "increase_allocation", "description": "Consider increasing allocation to UK gilts as safe haven.", "direction": "increase"},
    ],
    ("ftse_drawdown", "High"): [
        {"action_type": "rotate", "description": "Review cyclical exposure and consider partial rotation to defensives.", "direction": "rotate"},
    ],
    ("ftse_drawdown", "Medium"): [
        {"action_type": "monitor", "description": "FTSE drawdown approaching elevated levels — monitor positions.", "direction": None},
    ],
    ("ftse_drawdown", "Low"): [
        {"action_type": "monitor", "description": "FTSE pullback beginning — no action required, continue monitoring.", "direction": None},
    ],
    ("vix_spike", "High"): [
        {"action_type": "reduce_exposure", "description": "Elevated volatility — consider reducing risk across the portfolio.", "direction": "decrease"},
        {"action_type": "increase_allocation", "description": "Increase allocation to gilts or cash during elevated VIX.", "direction": "increase"},
    ],
    ("yield_curve_inversion", "High"): [
        {"action_type": "rotate", "description": "Yield curve inversion historically precedes recession — rotate toward defensive dividend stocks.", "direction": "rotate"},
    ],
    ("commodity_spike", "High"): [
        {"action_type": "investigate", "description": "Commodity spike detected. Review energy and materials exposure.", "direction": None},
    ],
    ("bond_yield_shock", "High"): [
        {"action_type": "reduce_exposure", "description": "Rising gilt yields reduce bond-proxy dividend stock attractiveness — review positions.", "direction": "decrease"},
    ],
}


def generate_actions(alert: Alert) -> list[dict]:
    """Generate and persist recommended actions for an alert."""
    key = (alert.type, alert.severity)
    action_defs = ACTION_MAP.get(key, [])
    actions = []
    for defn in action_defs:
        action = create_action(
            alert_id=alert.id,
            action_type=defn["action_type"],
            description=defn["description"],
            direction=defn.get("direction"),
        )
        actions.append(action)
    return actions


def process_alert(payload: dict) -> Alert | None:
    """
    Process a raw alert payload through the dedup/escalation lifecycle.

    Returns the persisted Alert if it should proceed, or None if suppressed.
    """
    alert_type = payload["type"]
    severity = payload["severity"]
    asset = payload.get("asset")
    message = payload["message"]

    existing = get_recent_alert(alert_type, asset, within_hours=24)

    if existing:
        if not severity_increased(existing.severity, severity):
            # Duplicate — suppress
            suppress_alert(existing.id, suppressed_until=now() + timedelta(hours=24))
            return None
        # Escalation — allow through

    alert = create_alert(
        type=alert_type,
        severity=severity,
        asset=asset,
        message=message,
    )
    generate_actions(alert)
    return alert


def route(alert: Alert) -> str:
    """Return routing destination based on severity."""
    if alert.severity in ("Critical", "High"):
        return "explain_and_notify_immediate"
    elif alert.severity == "Medium":
        return "digest_queue"
    else:
        return "dashboard_only"
