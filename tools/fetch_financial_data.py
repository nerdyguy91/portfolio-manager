"""
Fetches weekly financial data using yfinance:
  - EPS (trailing twelve months)
  - Trailing annual dividend per share
  - Market cap
  - Dividend history (last 8 quarters)

Writes results to the financial_data table.
"""

import json
import yfinance as yf
from tools.db import insert_financial_data, get_portfolio, init_db


def fetch_financials(ticker: str) -> dict:
    """Return EPS, dividend_per_share, market_cap for a ticker."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "eps": info.get("trailingEps"),
            "dividend_per_share": info.get("trailingAnnualDividendRate"),
            "market_cap": info.get("marketCap"),
        }
    except Exception as e:
        print(f"[fetch_financials] Failed for {ticker}: {e}")
        return {"eps": None, "dividend_per_share": None, "market_cap": None}


def fetch_dividend_history(ticker: str) -> list[dict]:
    """Return list of {date, dividend} dicts, most recent 8 entries."""
    try:
        divs = yf.Ticker(ticker).dividends
        if divs.empty:
            return []
        recent = divs.tail(8)
        return [
            {"date": str(date.date()), "dividend": float(value)}
            for date, value in recent.items()
        ]
    except Exception as e:
        print(f"[fetch_dividend_history] Failed for {ticker}: {e}")
        return []


def run():
    """Fetch financial data for all portfolio tickers and persist to DB."""
    portfolio = get_portfolio()
    results = {}
    for holding in portfolio:
        ticker = holding.ticker
        financials = fetch_financials(ticker)
        history = fetch_dividend_history(ticker)
        insert_financial_data(
            ticker=ticker,
            eps=financials["eps"],
            dividend_per_share=financials["dividend_per_share"],
            market_cap=financials["market_cap"],
            dividend_history=json.dumps(history),
        )
        results[ticker] = {**financials, "dividend_history_entries": len(history)}
        print(f"  {ticker}: EPS={financials['eps']}, DPS={financials['dividend_per_share']}, "
              f"MCap={financials['market_cap']}")
    return results


if __name__ == "__main__":
    init_db()
    print("Fetching financial data...")
    run()
    print("Done.")
