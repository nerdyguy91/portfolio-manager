# Workflow 08: Notification Dispatch

## Objective

Deliver alerts to the user via email according to severity rules. Ensure Critical and High alerts are sent immediately with explanations and actions. Medium alerts are batched into a daily digest.

---

## Trigger

Called by `scheduler/runner.py` after the Alert Lifecycle workflow (06) and Explanation Engine (07) have completed for each alert in a run.

---

## Required Inputs

For immediate alerts:
- `alert` — Alert row from DB
- `explanation` — Validated explanation dict (or `None` if engine failed)
- `actions` — List of Action rows for this alert

For daily digest:
- `alerts` — List of Medium-severity Alert rows queued during the run

---

## Tool

`tools/email_dispatch.py`

---

## Dispatch Rules (FR30, FR31)

| Severity | Delivery Method | When |
|---|---|---|
| Critical | `send_immediate_alert()` | Immediately after explanation generated |
| High | `send_immediate_alert()` | Immediately after explanation generated |
| Medium | `send_daily_digest()` | End of run, batched with other Medium alerts |
| Low | Dashboard only | No email sent |

---

## Email Format

### Immediate Alert

**Subject:** `[{SEVERITY}] Portfolio Alert — {alert_type}`

**Body:**
```
Alert: {message}
Timestamp: {timestamp}

--- Explanation ---
What triggered this: {explanation.trigger}
Why it matters: {explanation.why_it_matters}

Suggested actions:
- {action 1}
- {action 2}

Recommended portfolio changes:
- {action.description} ({action.direction})
```

If explanation is None (engine failed): omit explanation section, still include actions.

---

### Daily Digest

**Subject:** `[DIGEST] Portfolio Monitor — {N} alerts today`

**Body:** Summary list of all Medium alerts with type, asset, message, and recommended action.

---

## SMTP Configuration

All credentials from `.env`:
- `SMTP_HOST`, `SMTP_PORT`
- `SMTP_USER`, `SMTP_PASS`
- `ALERT_EMAIL_TO` — recipient address

Tool uses `smtplib` with `STARTTLS`.

---

## Edge Cases

- If `ALERT_EMAIL_TO` is not set → log warning, skip dispatch (do not fail the run)
- If SMTP connection fails → log error, retry once; if still fails → log and continue (alert is in DB regardless)
- Empty digest queue → do not send empty digest email

---

## Confidence Policy

No LLM reasoning in this workflow. Email formatting and dispatch are fully deterministic.
