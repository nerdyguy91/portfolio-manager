"""
Portfolio health rule evaluation.

Checks per ticker:
  - Dividend cover (EPS / DPS)
  - CADI: Consecutive Annual Dividend Increases (streak breaks)
  - Yield spike: current yield > 2x sector average
  - Market cap < £300M

Returns alert payloads (dicts) or None when no alert is triggered.
"""

import json
from tools.db import get_portfolio, get_latest_financial, SessionLocal, Portfolio

MARKET_CAP_THRESHOLD_GBP = 300_000_000   # £300M
DIVIDEND_COVER_CRITICAL = 1.3
DIVIDEND_COVER_WARNING = 1.7
YIELD_SPIKE_MULTIPLIER = 2.0


def check_dividend_cover(ticker: str) -> dict | None:
    data = get_latest_financial(ticker)
    if not data or data.eps is None or data.dividend_per_share is None:
        return None
    if data.dividend_per_share == 0:
        return None

    cover = data.eps / data.dividend_per_share

    if cover < DIVIDEND_COVER_CRITICAL:
        return {
            "type": "dividend_cover",
            "severity": "Critical",
            "asset": ticker,
            "message": (f"{ticker}: Dividend cover is {cover:.2f}x (below critical threshold of "
                        f"{DIVIDEND_COVER_CRITICAL}x). EPS={data.eps:.2f}, DPS={data.dividend_per_share:.2f}."),
            "context": {"cover": cover, "eps": data.eps, "dps": data.dividend_per_share},
        }
    elif cover < DIVIDEND_COVER_WARNING:
        return {
            "type": "dividend_cover",
            "severity": "Medium",
            "asset": ticker,
            "message": (f"{ticker}: Dividend cover is {cover:.2f}x (below warning threshold of "
                        f"{DIVIDEND_COVER_WARNING}x). EPS={data.eps:.2f}, DPS={data.dividend_per_share:.2f}."),
            "context": {"cover": cover, "eps": data.eps, "dps": data.dividend_per_share},
        }
    return None


def check_cadi(ticker: str) -> dict | None:
    """
    Detects breaks in the consecutive annual dividend increase (CADI) streak.
    Uses the stored dividend_history JSON (up to 8 recent dividends).
    Compares the most recent full-year total to the prior full-year total.
    """
    data = get_latest_financial(ticker)
    if not data or not data.dividend_history:
        return None

    history = json.loads(data.dividend_history)
    if len(history) < 4:
        return None  # Not enough data

    # Sum last 4 entries vs prior 4 entries as annual proxy
    recent_annual = sum(e["dividend"] for e in history[-4:])
    prior_annual = sum(e["dividend"] for e in history[-8:-4]) if len(history) >= 8 else None

    if prior_annual is None or prior_annual == 0:
        return None

    if recent_annual < prior_annual:
        return {
            "type": "cadi_break",
            "severity": "Critical",
            "asset": ticker,
            "message": (f"{ticker}: Dividend cut detected. Annual dividend fell from "
                        f"{prior_annual:.4f} to {recent_annual:.4f}."),
            "context": {"recent_annual": recent_annual, "prior_annual": prior_annual},
        }
    elif recent_annual == prior_annual:
        return {
            "type": "cadi_break",
            "severity": "Medium",
            "asset": ticker,
            "message": (f"{ticker}: No year-over-year dividend increase detected. "
                        f"Annual dividend flat at ~{recent_annual:.4f}."),
            "context": {"recent_annual": recent_annual, "prior_annual": prior_annual},
        }
    return None


def check_yield_spike(ticker: str) -> dict | None:
    """
    Triggers if current dividend yield > 2x the sector average yield.
    sector_avg_yield must be set manually on the portfolio holding.
    """
    data = get_latest_financial(ticker)
    if not data or data.dividend_per_share is None or data.market_cap is None:
        return None

    with SessionLocal() as db:
        holding = db.get(Portfolio, ticker)

    if not holding or holding.sector_avg_yield is None:
        return None  # Cannot check without sector average

    # Price needed for yield; use market_cap / shares as proxy is unreliable —
    # instead derive from dividend_per_share and a yfinance price if available.
    # Here we rely on market_data for current price.
    from tools.db import get_market_data
    prices = get_market_data(ticker, limit=1)
    if not prices:
        return None
    current_price = prices[0].price
    if current_price == 0:
        return None

    current_yield = data.dividend_per_share / current_price
    threshold = holding.sector_avg_yield * YIELD_SPIKE_MULTIPLIER

    if current_yield > threshold:
        return {
            "type": "yield_spike",
            "severity": "High",
            "asset": ticker,
            "message": (f"{ticker}: Dividend yield of {current_yield:.2%} is more than "
                        f"2x the sector average ({holding.sector_avg_yield:.2%}). "
                        f"May signal elevated risk."),
            "context": {
                "current_yield": current_yield,
                "sector_avg_yield": holding.sector_avg_yield,
                "threshold": threshold,
            },
        }
    return None


def check_market_cap(ticker: str) -> dict | None:
    data = get_latest_financial(ticker)
    if not data or data.market_cap is None:
        return None

    if data.market_cap < MARKET_CAP_THRESHOLD_GBP:
        return {
            "type": "market_cap_low",
            "severity": "Medium",
            "asset": ticker,
            "message": (f"{ticker}: Market cap is £{data.market_cap:,.0f}, "
                        f"below the £300M minimum threshold."),
            "context": {"market_cap": data.market_cap},
        }
    return None


def run_all() -> list[dict]:
    """Run all portfolio health checks for every holding. Returns list of alert payloads."""
    portfolio = get_portfolio()
    alerts = []
    for holding in portfolio:
        for check in [check_dividend_cover, check_cadi, check_yield_spike, check_market_cap]:
            result = check(holding.ticker)
            if result:
                alerts.append(result)
    return alerts
