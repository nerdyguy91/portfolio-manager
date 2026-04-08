"""
APScheduler job runner.

Two recurring jobs:
  - Daily (weekdays at 18:00 UTC, after market close):
      fetch market data → market stress → regime classify → alert lifecycle → notify

  - Weekly (Monday at 07:00 UTC, before market open):
      fetch financial + macro data → portfolio health → macro checks → risk score → notify
"""

import sys
import os

# Allow imports from project root when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from tools.db import init_db, log_run, get_active_alerts
from tools.fetch_market_data import run as fetch_market
from tools.fetch_financial_data import run as fetch_financial
from tools.fetch_macro_data import run as fetch_macro
from tools.rules.market_stress import run_all as market_stress_checks
from tools.rules.portfolio_health import run_all as portfolio_health_checks
from tools.rules.macro_check import run_all as macro_checks
from tools.rules.regime_classifier import run as classify_regime
from tools.alert_lifecycle import process_alert, route
from tools.risk_score import compute_risk_score
from tools.explanation_tool import generate_explanation
from tools.email_dispatch import send_immediate_alert, send_daily_digest
from tools.db import get_actions_for_alert


def _handle_alert_payloads(payloads: list[dict], regime: str):
    """Process alert payloads through the full lifecycle."""
    digest_queue = []

    for payload in payloads:
        alert = process_alert(payload)
        if alert is None:
            continue  # Suppressed duplicate

        routing = route(alert)

        if routing == "explain_and_notify_immediate":
            context = payload.get("context", {})
            explanation = generate_explanation(alert, context, regime)
            actions = get_actions_for_alert(alert.id)
            send_immediate_alert(alert, explanation, actions)

        elif routing == "digest_queue":
            digest_queue.append(alert)

        # Low severity → dashboard only, no further action

    if digest_queue:
        send_daily_digest(digest_queue)


def daily_job():
    """Daily monitoring run: market data, stress checks, regime, notifications."""
    print("[runner] Starting daily job...")
    log_run("daily", "started")
    try:
        fetch_market()

        stress_alerts = market_stress_checks()
        regime_result = classify_regime()
        regime = regime_result["regime"]

        _handle_alert_payloads(stress_alerts, regime)

        score = compute_risk_score()
        log_run("daily", "completed", regime_state=regime, risk_score=score)
        print(f"[runner] Daily job complete. Regime={regime}, Score={score}")

    except Exception as e:
        log_run("daily", "failed", error=str(e))
        print(f"[runner] Daily job FAILED: {e}")
        raise


def weekly_job():
    """Weekly monitoring run: financial + macro data, health checks, risk score."""
    print("[runner] Starting weekly job...")
    log_run("weekly", "started")
    try:
        fetch_financial()
        fetch_macro()

        health_alerts = portfolio_health_checks()
        macro_alert_list = macro_checks()
        regime_result = classify_regime()
        regime = regime_result["regime"]

        all_alerts = health_alerts + macro_alert_list
        _handle_alert_payloads(all_alerts, regime)

        score = compute_risk_score()
        log_run("weekly", "completed", regime_state=regime, risk_score=score)
        print(f"[runner] Weekly job complete. Regime={regime}, Score={score}")

    except Exception as e:
        log_run("weekly", "failed", error=str(e))
        print(f"[runner] Weekly job FAILED: {e}")
        raise


def run_now(job: str = "daily"):
    """Run a job immediately (useful for testing)."""
    init_db()
    if job == "weekly":
        weekly_job()
    else:
        daily_job()


def start_scheduler():
    init_db()
    scheduler = BlockingScheduler(timezone="UTC")

    # Daily: weekdays at 18:00 UTC (London market close + buffer)
    scheduler.add_job(daily_job, CronTrigger(day_of_week="mon-fri", hour=18, minute=0))

    # Weekly: Monday at 07:00 UTC
    scheduler.add_job(weekly_job, CronTrigger(day_of_week="mon", hour=7, minute=0))

    print("[runner] Scheduler started. Jobs:")
    print("  - Daily:  Mon–Fri at 18:00 UTC")
    print("  - Weekly: Monday at 07:00 UTC")
    print("  Press Ctrl+C to stop.")
    scheduler.start()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Portfolio monitoring scheduler")
    parser.add_argument("--run-now", choices=["daily", "weekly"],
                        help="Run a job immediately instead of starting the scheduler")
    args = parser.parse_args()

    if args.run_now:
        run_now(args.run_now)
    else:
        start_scheduler()
