# Workflow 01: Data Ingestion

## Objective

Fetch and persist all market, financial, and macro data required for downstream rule evaluation. No alert generation occurs in this workflow.

---

## Trigger

- **Daily run** (Mon–Fri, 18:00 UTC): market data only
- **Weekly run** (Monday, 07:00 UTC): financial + macro data only

---

## Daily Run

### Required Inputs

- Portfolio tickers from `portfolio` table

### Tools to Call (in order)

1. `tools/fetch_market_data.py::run()`
   - Fetches daily close price for each portfolio ticker via yfinance
   - Fetches FTSE 100 index price (ticker: `^FTSE`)
   - Fetches VIX (ticker: `^VIX`)
   - Writes all to `market_data` table

### Expected Output

Rows inserted to `market_data` with:
- `ticker`: each portfolio ticker, plus `^FTSE` and `^VIX`
- `price`: float
- `timestamp`: UTC datetime (date-precision for daily data)

### Edge Cases

- If yfinance returns no data for a ticker (e.g. market holiday, delisted): log warning, skip ticker, continue with others
- If `^FTSE` or `^VIX` fetch fails: log error — downstream market stress check will fail gracefully

---

## Weekly Run

### Required Inputs

- Portfolio tickers from `portfolio` table
- FRED API key from `.env`

### Tools to Call (in order)

1. `tools/fetch_financial_data.py::run()`
   - For each portfolio ticker: fetches EPS, trailing dividend per share, market cap, dividend history
   - Writes to `financial_data` table (append-only)

2. `tools/fetch_macro_data.py::run()`
   - Fetches FRED series: DGS2 (US 2Y yield), DGS10 (US 10Y yield), IRLTLT01GBM156N (UK 10Y gilt), PPIACO (commodity index)
   - Writes to `macro_data` table (append-only, deduplicates by indicator + timestamp)

### Expected Output

New rows in `financial_data` per ticker:
- `eps`, `dividend_per_share`, `market_cap`, `dividend_history` (JSON array), `timestamp`

New rows in `macro_data` per indicator:
- `indicator`, `value`, `timestamp`

### Edge Cases

- If yfinance returns null EPS or dividend (common for some tickers): write null, downstream rules handle gracefully
- If FRED API rate-limits or returns error: log error, abort macro fetch — macro check workflow will skip if data is missing
- Never overwrite existing rows — append only

---

## Confidence Policy

No LLM reasoning in this workflow. All operations are deterministic. No confidence threshold required.

---

## Audit

All runs logged to `run_log` table via `tools/db.py::log_run()` with status `started` / `completed` / `failed`.
