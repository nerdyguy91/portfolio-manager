import json
from fastapi import APIRouter
from tools.db import get_active_alerts, get_actions_for_alert

router = APIRouter()


@router.get("")
def list_alerts(limit: int = 50):
    alerts = get_active_alerts(limit=limit)
    result = []
    for alert in alerts:
        actions = get_actions_for_alert(alert.id)
        explanation = None
        if alert.explanation:
            try:
                explanation = json.loads(alert.explanation)
            except Exception:
                pass
        result.append({
            "id": alert.id,
            "type": alert.type,
            "severity": alert.severity,
            "asset": alert.asset,
            "message": alert.message,
            "explanation": explanation,
            "needs_review": alert.needs_review,
            "risk_score": alert.risk_score,
            "timestamp": alert.timestamp.isoformat(),
            "actions": [
                {
                    "action_type": a.action_type,
                    "description": a.description,
                    "direction": a.direction,
                }
                for a in actions
            ],
        })
    return result
