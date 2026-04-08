from fastapi import APIRouter
from tools.db import get_market_data
from tools.rules.market_stress import compute_drawdown

router = APIRouter()


@router.get("")
def get_market():
    ftse_rows = get_market_data("^FTSE", limit=90)
    vix_rows = get_market_data("^VIX", limit=1)
    dd = compute_drawdown()

    return {
        "ftse": {
            "current": ftse_rows[0].price if ftse_rows else None,
            "drawdown": dd,
            "history": [
                {"timestamp": r.timestamp.isoformat(), "price": r.price}
                for r in reversed(ftse_rows)
            ],
        },
        "vix": vix_rows[0].price if vix_rows else None,
    }
