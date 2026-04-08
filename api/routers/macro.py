from fastapi import APIRouter
from tools.db import get_latest_macro, get_macro_series

router = APIRouter()

INDICATORS = ["us_2y_yield", "us_10y_yield", "uk_10y_gilt", "commodity_index"]


@router.get("")
def get_macro():
    result = {}
    for indicator in INDICATORS:
        latest = get_latest_macro(indicator)
        series = get_macro_series(indicator, limit=90)
        result[indicator] = {
            "latest": latest.value if latest else None,
            "latest_date": latest.timestamp.isoformat() if latest else None,
            "history": [
                {"timestamp": r.timestamp.isoformat(), "value": r.value}
                for r in reversed(series)
            ],
        }

    # Derived: yield spread (10Y - 2Y)
    y2 = result["us_2y_yield"]["latest"]
    y10 = result["us_10y_yield"]["latest"]
    if y2 is not None and y10 is not None:
        result["yield_spread"] = round(y10 - y2, 4)
        result["yield_curve_inverted"] = y2 > y10
    else:
        result["yield_spread"] = None
        result["yield_curve_inverted"] = None

    return result
