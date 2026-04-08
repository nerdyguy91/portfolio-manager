"""
Fetches weekly macro data from the FRED API:
  - DGS2        → US 2-year Treasury yield
  - DGS10       → US 10-year Treasury yield
  - IRLTLT01GBM156N → UK 10-year gilt yield
  - PPIACO      → PPI All Commodities (commodity index proxy)

Writes results to the macro_data table.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv
from fredapi import Fred
from tools.db import insert_macro_data, init_db
import ssl
import certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

load_dotenv()

SERIES = {
    "us_2y_yield": "DGS2",
    "us_10y_yield": "DGS10",
    "uk_10y_gilt": "IRLTLT01GBM156N",
    "commodity_index": "PPIACO",
}

# How many days back to fetch (covers the 5-consecutive-day yield curve check
# and the 3-month window for commodity/bond checks)
LOOKBACK_DAYS = 100


def get_fred() -> Fred:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise EnvironmentError("FRED_API_KEY not set in environment.")
    return Fred(api_key=api_key)


def fetch_series(fred: Fred, indicator: str, series_id: str) -> list[dict]:
    """Fetch a FRED series and return [{date, value}] for the lookback window."""
    from datetime import date
    end = date.today()
    start = end - timedelta(days=LOOKBACK_DAYS)
    try:
        data = fred.get_series(series_id, observation_start=start, observation_end=end)
        data = data.dropna()
        return [{"date": str(d.date()), "value": float(v)} for d, v in data.items()]
    except Exception as e:
        print(f"[fetch_macro] Failed for {indicator} ({series_id}): {e}")
        return []


def run():
    """Fetch all macro series and persist to DB."""
    from datetime import datetime
    fred = get_fred()
    results = {}
    for indicator, series_id in SERIES.items():
        entries = fetch_series(fred, indicator, series_id)
        for entry in entries:
            ts = datetime.strptime(entry["date"], "%Y-%m-%d")
            insert_macro_data(indicator, entry["value"], ts)
        results[indicator] = entries[-1] if entries else None
        latest = entries[-1] if entries else "N/A"
        print(f"  {indicator}: {latest}")
    return results


if __name__ == "__main__":
    init_db()
    print("Fetching macro data...")
    run()
    print("Done.")
