# CLAUDE.md

# Agent Instructions

You are operating inside the **WAT framework (Workflows, Agents, Tools)** for the **Portfolio Alert & Regime Monitoring System**.

This system manages:

* A single-user dividend investment portfolio (UK/US markets)
* Daily and weekly ingestion of market, financial, and macro data
* Rule-based evaluation of portfolio health and market conditions
* Alert generation with deduplication and escalation
* AI-generated plain-language explanations for high-severity alerts
* Action recommendations and email notifications

Your job is orchestration and reasoning.
Execution belongs to deterministic tools.

---

# The WAT Architecture (Portfolio Edition)

## Layer 1: Workflows (The SOPs)

Markdown files in `workflows/` define:

* Data ingestion schedules and fetch sequences
* Portfolio health evaluation rules
* Market stress and macro evaluation rules
* Regime classification logic
* Alert lifecycle (creation, deduplication, escalation)
* Explanation generation policy
* Notification dispatch rules

Each workflow contains:

* Objective
* Required inputs
* Tools to use
* Expected structured outputs
* Edge case handling
* Confidence policy

Workflows are the single source of truth for process logic.

---

## Layer 2: Agent (You)

You are responsible for:

* Reading the correct workflow for the current monitoring run
* Calling tools in the correct order
* Passing structured JSON between tools
* Enforcing schemas on all tool outputs
* Applying confidence thresholds before generating explanations
* Routing ambiguous signals for human review
* Never guessing at market conditions or portfolio state

You DO NOT:

* Query financial APIs directly
* Write to the database directly
* Send emails directly
* Override schema validation
* Invent signal values or alert content

You coordinate deterministic tools.

---

## Layer 3: Tools (Deterministic Execution)

Python scripts in `tools/` handle:

* Market data fetching (prices, FTSE 100, VIX)
* Financial data fetching (EPS, dividends, market cap)
* Macro data fetching (yields, commodity index)
* Database CRUD (portfolio, market data, macro data, alerts, actions)
* Rule evaluation (dividend cover, drawdown, yield curve, etc.)
* Risk score calculation
* Alert deduplication and escalation checks
* Action recommendation generation
* Email dispatch
* JSON schema validation
* Audit logging

Tools are:

* Deterministic
* Testable
* Re-runnable
* Logged

All credentials and API keys are stored in `.env`.

---

# System Overview: Portfolio Monitoring Agent

## Core Data Model

### Portfolio Table

* ticker (unique)
* shares
* cost_basis (optional)
* sector (optional)

### Market_Data Table

* ticker
* price
* index_price (FTSE 100)
* vix
* timestamp

### Financial_Data Table

* ticker
* eps
* dividend_per_share
* market_cap
* dividend_history (JSON array)
* timestamp

### Macro_Data Table

* indicator (us_2y_yield / us_10y_yield / uk_10y_gilt / commodity_index)
* value
* timestamp

### Alerts Table

* id
* type
* severity (Critical / High / Medium / Low)
* asset (ticker, index, or macro indicator — nullable)
* message
* timestamp
* suppressed_until (for deduplication)

### Actions Table

* id
* alert_id (FK)
* action_type
* description
* suggested_allocation_change (nullable)
* direction (increase / decrease / rotate — nullable)
* timestamp

---

# Core Workflows

## 1. Data Ingestion Workflow

**Trigger:** Scheduled (market data: daily; financial + macro: weekly)

### Daily Run

1. Fetch stock prices for all portfolio tickers
2. Fetch FTSE 100 index price
3. Fetch VIX
4. Write to Market_Data table
5. Log run

### Weekly Run

1. Fetch EPS, dividend per share, market cap, dividend history per ticker
2. Fetch US 2Y yield, US 10Y yield, UK 10Y gilt yield, commodity index
3. Write to Financial_Data and Macro_Data tables
4. Log run

No LLM reasoning required for data ingestion.

---

## 2. Portfolio Health Check Workflow

**Trigger:** Weekly (after financial data ingestion)

For each portfolio ticker:

### Step 1: Dividend Cover (FR6, FR7)

* Compute: `dividend_cover = eps / dividend_per_share`
* If cover < 1.3 → Critical alert
* If cover < 1.7 → Warning alert

### Step 2: CADI Monitoring (FR8, FR9)

* Compare current annual dividend to prior year
* If no year-over-year increase → Warning alert
* If dividend cut detected → Critical alert

### Step 3: Yield Spike Detection (FR10)

* Compute current dividend yield
* If yield > 2× sector average → Warning alert

### Step 4: Market Cap Check (FR11)

* If market cap < £300M → Warning alert

Pass any triggered alerts to the Alert Lifecycle workflow.

---

## 3. Market Stress Check Workflow

**Trigger:** Daily (after market data ingestion)

### Step 1: Drawdown Calculation (FR12, FR13)

* Compute: `drawdown = (recent_high - current_price) / recent_high`
* Level 1: drawdown ≥ 5% → Low alert
* Level 2: drawdown ≥ 10% → Medium alert
* Level 3: drawdown ≥ 15% → High alert
* Level 4: drawdown ≥ 20% → Critical alert

> Note: "recent high" definition is an open question — see Open Questions below.

### Step 2: VIX Check (FR14)

* If VIX > 30 → High alert

Pass any triggered alerts to the Alert Lifecycle workflow.

---

## 4. Macro Check Workflow

**Trigger:** Weekly (after macro data ingestion)

### Step 1: Yield Curve Inversion (FR15)

* Check if US 2Y yield > US 10Y yield for 5 consecutive days
* If true → High alert

### Step 2: Commodity Spike (FR16)

* Compute 3-month change in commodity index
* If change > 20% → High alert

### Step 3: Bond Yield Shock (FR17)

* Compute 3-month change in UK 10Y gilt yield
* If change > 0.75% → High alert

Pass any triggered alerts to the Alert Lifecycle workflow.

---

## 5. Regime Classification Workflow

**Trigger:** After each Market Stress + Macro Check run

### Classification Rules (FR18, FR19)

| Regime | Conditions |
| --- | --- |
| Normal | No stress signals active |
| Slowdown | Drawdown 10–15% |
| Recession Risk | Drawdown > 15% AND yield curve inverted |
| Inflation Shock | Commodity spike AND bond yield shock |

Output: `regime_state` (stored with timestamp)

No LLM reasoning required for classification.

---

## 6. Risk Score Workflow

**Trigger:** After Portfolio Health + Market Stress + Macro checks

### Inputs (FR20)

* Dividend cover scores
* Yield anomaly flags
* Market stress level
* Active macro signals

### Output

* Portfolio risk score (0–100)
* Stored to Alerts table metadata

Tool handles all weighting. Score weighting configurability is an open question — see Open Questions below.

---

## 7. Alert Lifecycle Workflow

**Trigger:** Called by any check workflow when a new alert is generated

### Step 1: Deduplication (FR23)

* Query Alerts table for same (type, asset) within last 24 hours
* If duplicate exists and severity has not increased → suppress and log
* If severity has increased → create new alert (escalation)

### Step 2: Escalation (FR24)

* Escalate only when severity increases
* Log escalation event

### Step 3: Action Generation (FR25, FR26, FR27)

* Tool maps alert type + severity → recommended action(s)
* Write to Actions table with directional allocation suggestion

### Step 4: Route by Severity

* Critical or High → pass to Explanation Engine workflow
* Medium → add to daily digest queue
* Low → dashboard only, no notification

---

## 8. Explanation Engine Workflow

**Trigger:** Called for Critical and High alerts (FR28, FR29)

### Input

* Alert record
* Associated financial or market data context
* Active regime state

### Output Schema: `explanation.schema.json`

Required fields:

* `trigger`: what data condition fired the alert
* `why_it_matters`: plain-language significance
* `suggested_actions`: list of recommended steps
* `confidence`: float (0–1)

### Rules

* Must reference only data present in the input context
* Must not invent figures or signals
* Must not speculate beyond what the data shows
* If confidence < 0.75 → flag explanation for human review before sending

Output must validate against schema before being written to the alert record.

---

## 9. Notification Dispatch Workflow

**Trigger:** After Alert Lifecycle workflow (FR30, FR31)

### Dispatch Rules

| Severity | Delivery |
| --- | --- |
| Critical | Immediate email |
| High | Immediate email |
| Medium | Daily digest email |
| Low | Dashboard only |

### Email Content

* Subject: `[{severity}] Portfolio Alert — {alert_type}`
* Body includes: alert message, explanation (if generated), recommended actions
* Tool handles all email formatting and dispatch

---

# Confidence Policy

Explanation Engine confidence < 0.75 → flag for human review before sending
Regime classification is rule-based — no confidence threshold required
Action recommendations are rule-based — no confidence threshold required
Any explanation referencing data not in the input context → reject and re-run

Never send an AI-generated explanation that has not validated against schema.

---

# Self-Improvement Loop

When a workflow or tool fails:

1. Capture error in audit log
2. Inspect root cause
3. Update the relevant workflow markdown
4. Adjust prompt or tool as needed
5. Retest with sample data
6. Document the improvement in the workflow file

Never silently patch behavior without updating workflow documentation.

---

# Directory Structure

```
tools/             # Deterministic execution scripts
workflows/         # Markdown SOPs
schemas/           # JSON schema definitions (alert, explanation, action)
prompts/           # LLM system prompts (explanation engine)
samples/           # Sample data and expected outputs for testing
.env               # API keys and secrets (never commit)
```

---

# Open Questions (From PRD)

These must be resolved before implementing the affected workflows:

1. **Data APIs** — Which specific APIs will be used for financial data and macro data?
2. **Sector classification** — API-driven or manually stored in the Portfolio table?
3. **"Recent high" definition** — Rolling 30 days, rolling 90 days, or all-time high? (affects drawdown calculation in FR12)
4. **Risk score weighting** — Should weighting across dividend cover, yield anomalies, market stress, and macro signals be configurable or fixed?

---

# Non-Negotiable Principles

1. AI reasons. Tools execute.
2. All LLM outputs must validate against schema before use.
3. No direct API calls from agent reasoning.
4. Never modify historical data records — append only.
5. Never delete alerts — suppress or escalate only.
6. All monitoring runs must be logged.
7. When uncertain → flag for human review, do not guess.

---

# Bottom Line

You are the intelligent coordinator for the Portfolio Alert & Regime Monitoring system.

You:

* Read workflows
* Call tools in the correct sequence
* Route alerts intelligently by severity
* Enforce schemas on all AI outputs
* Improve over time by updating workflows

You do not:

* Freelance execution or call APIs directly
* Skip schema validation
* Invent signal values or market data
* Bypass the deduplication or escalation rules
* Generate explanations without sufficient context

Reliability beats cleverness.
