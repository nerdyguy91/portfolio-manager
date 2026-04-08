# Workflow 02: Portfolio Health Check

## Objective

Evaluate dividend sustainability and portfolio quality for each holding. Generate alert payloads for any breached thresholds. Pass all payloads to the Alert Lifecycle workflow.

---

## Trigger

Weekly (after financial data ingestion completes).

---

## Required Inputs

- `financial_data` table: latest EPS, dividend_per_share, market_cap, dividend_history per ticker
- `portfolio` table: ticker, sector, sector_avg_yield (for yield spike check)

---

## Steps

### Step 1: Dividend Cover Check (FR6, FR7)

**Tool:** `tools/rules/portfolio_health.py::check_dividend_cover(ticker)`

**Logic:**
```
dividend_cover = eps / dividend_per_share
```

| Condition | Alert Severity | Alert Type |
|---|---|---|
| cover < 1.3 | Critical | dividend_cover |
| cover < 1.7 | Warning (High) | dividend_cover |

**Edge cases:**
- If `eps` is null or negative → generate Critical alert (no cover computable)
- If `dividend_per_share` is null or 0 → skip (no dividend paid)

---

### Step 2: CADI Monitoring (FR8, FR9)

**Tool:** `tools/rules/portfolio_health.py::check_cadi(ticker)`

**Logic:**
- Parse `dividend_history` JSON array from latest financial_data row
- Compare most recent full-year total dividend to prior year total
- Detect streak break (no YoY increase) or cut (current < prior)

| Condition | Alert Severity | Alert Type |
|---|---|---|
| No YoY increase | Medium | cadi_streak_break |
| Dividend cut | Critical | dividend_cut |

**Edge cases:**
- If dividend_history has < 2 years of data → skip, log warning
- If dividend is new (< 1 year of history) → skip

---

### Step 3: Yield Spike Detection (FR10)

**Tool:** `tools/rules/portfolio_health.py::check_yield_spike(ticker)`

**Logic:**
```
current_yield = dividend_per_share / current_price
```
- `current_price` from latest `market_data` row for this ticker
- `sector_avg_yield` from `portfolio` table (manual input field)

| Condition | Alert Severity | Alert Type |
|---|---|---|
| current_yield > 2× sector_avg_yield | Medium | yield_spike |

**Edge cases:**
- If `sector_avg_yield` is null → skip this check (log warning: "sector_avg_yield not set for {ticker}")
- If `current_price` is null → skip

---

### Step 4: Market Cap Check (FR11)

**Tool:** `tools/rules/portfolio_health.py::check_market_cap(ticker)`

**Logic:**

| Condition | Alert Severity | Alert Type |
|---|---|---|
| market_cap < £300M (300_000_000) | Low | small_cap_warning |

**Edge cases:**
- If `market_cap` is null → skip
- Note: yfinance returns market cap in the stock's native currency. For UK tickers (`.L`), this is GBP pence — divide by 100 to get pounds, then compare to 300,000,000

---

## Output

List of alert payloads (dicts). Each payload passed individually to `Alert Lifecycle Workflow (06)`.

Empty list if no thresholds breached.

---

## Confidence Policy

No LLM reasoning. All rule evaluations are deterministic. No confidence threshold required.
