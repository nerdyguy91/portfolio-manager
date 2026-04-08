"""
Fetches daily market data using yfinance:
  - Individual stock prices for all portfolio tickers
  - FTSE 100 index price (^FTSE)
  - VIX (^VIX)

Writes results to the market_data table.
"""

import yfinance as yf
from tools.db import insert_market_data, get_portfolio, init_db, now


def fetch_prices(tickers: list[str]) -> dict[str, float]:
    """Return {ticker: latest_close_price} for each ticker."""
    result = {}
    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(period="2d")
            if not data.empty:
                result[ticker] = float(data["Close"].iloc[-1])
        except Exception as e:
            print(f"[fetch_prices] Failed for {ticker}: {e}")
    return result


def fetch_ftse() -> float | None:
    try:
        data = yf.Ticker("^FTSE").history(period="2d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
    except Exception as e:
        print(f"[fetch_ftse] Error: {e}")
    return None


def fetch_vix() -> float | None:
    try:
        data = yf.Ticker("^VIX").history(period="2d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
    except Exception as e:
        print(f"[fetch_vix] Error: {e}")
    return None


def run():
    """Fetch all market data and persist to DB."""
    ts = now()
    portfolio = get_portfolio()
    tickers = [h.ticker for h in portfolio]

    prices = fetch_prices(tickers)
    for ticker, price in prices.items():
        insert_market_data(ticker, price, ts)
        print(f"  {ticker}: {price:.4f}")

    ftse = fetch_ftse()
    if ftse is not None:
        insert_market_data("^FTSE", ftse, ts)
        print(f"  ^FTSE: {ftse:.2f}")

    vix = fetch_vix()
    if vix is not None:
        insert_market_data("^VIX", vix, ts)
        print(f"  ^VIX: {vix:.2f}")

    return {"prices": prices, "ftse": ftse, "vix": vix}


if __name__ == "__main__":
    init_db()
    print("Fetching market data...")
    result = run()
    print("Done.", result)
