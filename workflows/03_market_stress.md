# Workflow 03: Market Stress Check

## Objective

Evaluate FTSE 100 drawdown and VIX levels. Generate alert payloads for any stress thresholds breached. Pass payloads to the Alert Lifecycle workflow.

---

## Trigger

Daily (after market data ingestion completes).

---

## Required Inputs

- `market_data` table: last 90 days of `^FTSE` prices
- `market_data` table: latest `^VIX` price

---

## Steps

### Step 1: Drawdown Calculation (FR12, FR13)

**Tool:** `tools/rules/market_stress.py::check_drawdown()`

**Logic:**
```
recent_high = max(^FTSE prices over last 90 days)
current_price = most recent ^FTSE price
drawdown = (recent_high - current_price) / recent_high
```

| Level | Condition | Alert Severity | Alert Type |
|---|---|---|---|
| 1 | drawdown ≥ 5% | Low | ftse_drawdown |
| 2 | drawdown ≥ 10% | Medium | ftse_drawdown |
| 3 | drawdown ≥ 15% | High | ftse_drawdown |
| 4 | drawdown ≥ 20% | Critical | ftse_drawdown |

Only the **highest** triggered level generates a single alert (not multiple).

Alert payload context must include: `drawdown_pct`, `current_price`, `recent_high`, `window_days=90`

**Edge cases:**
- If fewer than 5 days of FTSE data in DB → skip drawdown check, log warning
- If current_price equals recent_high (new high) → drawdown = 0%, no alert

---

### Step 2: VIX Check (FR14)

**Tool:** `tools/rules/market_stress.py::check_vix()`

**Logic:**

| Condition | Alert Severity | Alert Type |
|---|---|---|
| VIX > 30 | High | vix_elevated |

Alert payload context must include: `vix_value`

**Edge cases:**
- If no VIX data in DB → skip, log warning

---

## Output

List of 0–2 alert payloads. Each passed individually to `Alert Lifecycle Workflow (06)`.

Also pass drawdown value and VIX value to `Regime Classification Workflow (05)`.

---

## Confidence Policy

No LLM reasoning. All rule evaluations are deterministic. No confidence threshold required.
