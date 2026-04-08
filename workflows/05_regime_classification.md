# Workflow 05: Regime Classification

## Objective

Classify the current market regime using rule-based logic. Store the result to the run log. The regime state is used as context input to the Explanation Engine.

---

## Trigger

After each Market Stress Check (daily) and Macro Check (weekly) run completes.

---

## Required Inputs

| Input | Source | Type |
|---|---|---|
| `drawdown` | Market Stress Check output | float (0.0–1.0) |
| `yield_inverted` | Macro Check output | bool |
| `commodity_spike` | Macro Check output | bool |
| `bond_shock` | Macro Check output | bool |

On daily runs (no macro check): use `yield_inverted=False`, `commodity_spike=False`, `bond_shock=False` unless a macro alert is currently active in the `alerts` table.

---

## Tool

`tools/rules/regime_classifier.py::run()`

---

## Classification Rules (FR18, FR19)

Evaluated in priority order (first match wins):

| Priority | Regime | Conditions |
|---|---|---|
| 1 | Inflation Shock | `commodity_spike AND bond_shock` |
| 2 | Recession Risk | `drawdown > 0.15 AND yield_inverted` |
| 3 | Slowdown | `0.10 ≤ drawdown ≤ 0.15` |
| 4 | Normal | None of the above |

---

## Output

```json
{
  "regime": "Normal | Slowdown | Recession Risk | Inflation Shock",
  "drawdown": 0.07,
  "yield_inverted": false,
  "commodity_spike": false,
  "bond_shock": false,
  "timestamp": "2026-04-08T18:00:00"
}
```

Regime string stored to `run_log.regime_state` for the current run.

---

## Downstream Use

The `regime` string is passed as context to the Explanation Engine (Workflow 07) for all Critical and High alerts in the same run.

---

## Confidence Policy

No LLM reasoning. Classification is fully deterministic. No confidence threshold required.
