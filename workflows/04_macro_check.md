# Workflow 04: Macro Check

## Objective

Evaluate macroeconomic signals — yield curve inversion, commodity spike, bond yield shock. Generate alert payloads for breached thresholds. Pass payloads to the Alert Lifecycle workflow.

---

## Trigger

Weekly (after macro data ingestion completes).

---

## Required Inputs

- `macro_data` table: `us_2y_yield` and `us_10y_yield` — last 10 rows (for consecutive day check)
- `macro_data` table: `commodity_index` — last ~95 days (for 3-month change)
- `macro_data` table: `uk_10y_gilt` — last ~95 days (for 3-month change)

---

## Steps

### Step 1: Yield Curve Inversion (FR15)

**Tool:** `tools/rules/macro_check.py::check_yield_curve_inversion()`

**Logic:**
- Fetch last 10 rows of `us_2y_yield` and `us_10y_yield` ordered by timestamp descending
- Check if `us_2y_yield > us_10y_yield` for the 5 most recent consecutive rows

| Condition | Alert Severity | Alert Type |
|---|---|---|
| US 2Y > US 10Y for 5 consecutive days | High | yield_curve_inversion |

Alert context: `us_2y_latest`, `us_10y_latest`, `spread`, `consecutive_days_inverted`

**Edge cases:**
- If fewer than 5 rows available → skip, log warning
- FRED macro data is weekly — "5 consecutive" applies to the 5 most recent weekly observations

---

### Step 2: Commodity Spike (FR16)

**Tool:** `tools/rules/macro_check.py::check_commodity_spike()`

**Logic:**
```
3_month_change = (current_value - value_90_days_ago) / value_90_days_ago
```

| Condition | Alert Severity | Alert Type |
|---|---|---|
| 3-month change > 20% | High | commodity_spike |

Alert context: `current_value`, `value_90d_ago`, `pct_change`

**Edge cases:**
- If no data from ~90 days ago exists (DB too new) → use oldest available, note in context
- If only 1 data point exists → skip

---

### Step 3: Bond Yield Shock (FR17)

**Tool:** `tools/rules/macro_check.py::check_bond_yield_shock()`

**Logic:**
```
3_month_change = current_uk_gilt - uk_gilt_90_days_ago  (absolute, in percentage points)
```

| Condition | Alert Severity | Alert Type |
|---|---|---|
| 3-month change > 0.75 percentage points | High | bond_yield_shock |

Alert context: `current_yield`, `yield_90d_ago`, `absolute_change`

**Edge cases:**
- Same as commodity spike: use oldest available if 90-day lookback not yet populated

---

## Output

List of 0–3 alert payloads. Each passed individually to `Alert Lifecycle Workflow (06)`.

Also pass `yield_inverted`, `commodity_spike`, `bond_shock` boolean flags to `Regime Classification Workflow (05)`.

---

## Confidence Policy

No LLM reasoning. All rule evaluations are deterministic. No confidence threshold required.
