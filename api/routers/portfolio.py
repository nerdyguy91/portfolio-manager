from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from tools.db import upsert_portfolio, get_portfolio, get_latest_financial, get_market_data, SessionLocal, Portfolio

router = APIRouter()


class HoldingInput(BaseModel):
    ticker: str
    shares: float
    cost_basis: float | None = None
    sector: str | None = None
    sector_avg_yield: float | None = None


@router.get("")
def list_portfolio():
    holdings = get_portfolio()
    result = []
    for h in holdings:
        financials = get_latest_financial(h.ticker)
        prices = get_market_data(h.ticker, limit=1)
        raw_price = prices[0].price if prices else None
        import math
        current_price = None if (raw_price is None or math.isnan(raw_price)) else raw_price

        # Dividend cover
        cover = None
        if financials and financials.eps and financials.dividend_per_share:
            cover = financials.eps / financials.dividend_per_share if financials.dividend_per_share else None

        # Current yield
        current_yield = None
        if financials and financials.dividend_per_share and current_price:
            current_yield = financials.dividend_per_share / current_price

        result.append({
            "ticker": h.ticker,
            "shares": h.shares,
            "cost_basis": h.cost_basis,
            "sector": h.sector,
            "sector_avg_yield": h.sector_avg_yield,
            "current_price": current_price,
            "market_cap": financials.market_cap if financials else None,
            "eps": financials.eps if financials else None,
            "dividend_per_share": financials.dividend_per_share if financials else None,
            "dividend_cover": round(cover, 2) if cover else None,
            "current_yield": round(current_yield, 4) if current_yield else None,
        })
    return result


@router.post("")
def add_holding(body: HoldingInput):
    upsert_portfolio(
        ticker=body.ticker,
        shares=body.shares,
        cost_basis=body.cost_basis,
        sector=body.sector,
        sector_avg_yield=body.sector_avg_yield,
    )
    return {"status": "ok", "ticker": body.ticker}


@router.delete("/{ticker}")
def remove_holding(ticker: str):
    with SessionLocal() as db:
        holding = db.get(Portfolio, ticker)
        if not holding:
            raise HTTPException(status_code=404, detail="Ticker not found")
        db.delete(holding)
        db.commit()
    return {"status": "ok", "ticker": ticker}
