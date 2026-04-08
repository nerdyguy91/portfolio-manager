# Workflow 06: Alert Lifecycle

## Objective

Process every alert payload through deduplication, escalation, action generation, and severity-based routing. Ensure no duplicate noise and that every alert that reaches the user is actionable.

---

## Trigger

Called by any check workflow (Portfolio Health, Market Stress, Macro Check) when a new alert payload is generated.

---

## Required Inputs

A single alert payload dict:

```json
{
  "type": "dividend_cover",
  "severity": "Critical",
  "asset": "LGEN.L",
  "message": "Dividend cover for LGEN.L is 1.1 (below critical threshold of 1.3)",
  "context": {
    "eps": 0.22,
    "dividend_per_share": 0.20,
    "cover": 1.1
  }
}
```

---

## Steps

### Step 1: Deduplication (FR23)

**Tool:** `tools/alert_lifecycle.py::process_alert(payload)`

- Query `alerts` table for existing alert with same `(type, asset)` where `timestamp >= now - 24h` and `suppressed = False`
- **If found and severity has NOT increased:**
  - Suppress new alert (log suppression, return `None`)
  - Do not create a new DB row
- **If found and severity HAS increased:**
  - Create new alert row (escalation — see Step 2)
- **If not found:**
  - Create new alert row

**Severity order (low to high):** Low → Medium → High → Critical

---

### Step 2: Escalation (FR24)

Triggered only when severity increases (Step 1 detects escalation).

- Create new alert with escalation flag
- Log escalation event to `run_log`
- Continue to Step 3

---

### Step 3: Action Generation (FR25, FR26, FR27)

**Tool:** `tools/alert_lifecycle.py::generate_actions(alert)`

Maps `(alert_type, severity)` → action descriptions and directional allocation suggestion.

| Alert Type | Severity | Actions Generated |
|---|---|---|
| dividend_cover | Critical | Investigate dividend sustainability; consider reducing position |
| dividend_cover | High | Monitor EPS trend; review position size |
| dividend_cut | Critical | Immediate review; consider full exit |
| cadi_streak_break | Medium | Flag for quarterly review |
| yield_spike | Medium | Investigate whether yield reflects distress or mispricing |
| small_cap_warning | Low | Note liquidity risk; monitor news |
| ftse_drawdown | Critical | Consider reducing equity exposure; review defensive allocation |
| ftse_drawdown | High | Review portfolio hedges; avoid adding to cyclicals |
| ftse_drawdown | Medium | Monitor; no action required yet |
| ftse_drawdown | Low | Informational only |
| vix_elevated | High | Reduce new position sizing; consider short-term hedges |
| yield_curve_inversion | High | Consider rotating into shorter-duration bonds; review cyclical exposure |
| commodity_spike | High | Review commodity-exposed holdings; consider inflation-linked assets |
| bond_yield_shock | High | Review duration risk in fixed income; gilts may reprice |

Actions written to `actions` table with `alert_id` FK.

---

### Step 4: Route by Severity

| Severity | Routing |
|---|---|
| Critical | `explain_and_notify_immediate` → pass to Explanation Engine (07), then email |
| High | `explain_and_notify_immediate` → pass to Explanation Engine (07), then email |
| Medium | `digest_queue` → add to daily digest, no explanation generated |
| Low | `dashboard_only` → no email, no explanation |

---

## Output

- Alert row created in `alerts` table (or suppressed)
- Action rows created in `actions` table
- Routing decision returned to caller (`scheduler/runner.py`)

---

## Confidence Policy

No LLM reasoning in this workflow. All deduplication, escalation, and action logic is deterministic.
