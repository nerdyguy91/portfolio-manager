# Workflow 07: Explanation Engine

## Objective

Generate a plain-language explanation for Critical and High alerts. Explanations must be grounded in the data provided, validated against schema, and flagged for human review if confidence is below threshold.

---

## Trigger

Called for every alert routed as `explain_and_notify_immediate` (severity: Critical or High).

---

## Required Inputs

```json
{
  "alert": {
    "id": 42,
    "type": "ftse_drawdown",
    "severity": "High",
    "asset": null,
    "message": "FTSE 100 drawdown is 16.2% from 90-day high",
    "timestamp": "2026-04-08T18:00:00"
  },
  "context": {
    "drawdown_pct": 0.162,
    "current_price": 7423.5,
    "recent_high": 8857.2,
    "window_days": 90
  },
  "regime": "Recession Risk"
}
```

---

## Tool

`tools/explanation_tool.py::generate_explanation(alert, context, regime)`

---

## Process

1. Load system prompt from `prompts/explanation_engine.md`
2. Construct user message containing the alert record, context data, and current regime
3. Call Claude API: `claude-sonnet-4-6` via `anthropic.Anthropic().messages.create()`
4. Parse JSON response
5. Validate against `schemas/explanation.schema.json`

---

## Output Schema (`schemas/explanation.schema.json`)

```json
{
  "trigger": "string — what data condition fired the alert",
  "why_it_matters": "string — plain-language significance for a dividend investor",
  "suggested_actions": ["string", "..."],
  "confidence": 0.0–1.0
}
```

All four fields are required. Validation failure → reject and log error (do not send).

---

## Confidence Policy

| Confidence | Action |
|---|---|
| ≥ 0.75 | Write explanation to `alerts.explanation`; proceed to notification |
| < 0.75 | Set `alerts.needs_review = True`; hold notification; flag for human review |

The explanation must:
- Reference only figures present in the input context
- Not invent signal values, prices, or forecasts
- Not speculate beyond what the data shows
- Be written for a non-technical dividend investor

If the explanation references data not present in the input context → reject, log, do not send.

---

## Error Handling

- If Claude API call fails → log error, skip explanation, still send notification with alert message only
- If JSON parse fails → log error, retry once; if still fails → send without explanation
- If schema validation fails → log error, do not attach explanation to alert

Never block a Critical alert notification due to explanation failure. Send alert message + actions without explanation if engine fails.
