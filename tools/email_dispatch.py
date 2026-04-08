"""
Email dispatch via SMTP.

Handles:
  - Immediate alerts (Critical / High) with explanation and actions
  - Daily digest for Medium alerts
"""

import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from tools.db import Alert, Action

load_dotenv()


def _smtp_config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", 587)),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASS", ""),
        "to": os.getenv("ALERT_EMAIL_TO", ""),
    }


def _send(subject: str, body_html: str, body_text: str):
    cfg = _smtp_config()
    if not cfg["user"] or not cfg["to"]:
        print("[email_dispatch] SMTP not configured — skipping send.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["user"]
    msg["To"] = cfg["to"]
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
        server.ehlo()
        server.starttls()
        server.login(cfg["user"], cfg["password"])
        server.sendmail(cfg["user"], cfg["to"], msg.as_string())
    print(f"[email_dispatch] Sent: {subject}")


def _format_actions(actions: list[Action]) -> str:
    if not actions:
        return "<p><em>No specific actions recommended.</em></p>"
    items = "".join(f"<li>{a.description}</li>" for a in actions)
    return f"<ul>{items}</ul>"


def _format_explanation(explanation_json: str | None) -> str:
    if not explanation_json:
        return ""
    try:
        exp = json.loads(explanation_json)
        actions_html = "".join(f"<li>{s}</li>" for s in exp.get("suggested_actions", []))
        return f"""
        <div style="background:#f8f9fa;padding:12px;border-left:4px solid #6c757d;margin:12px 0;">
          <p><strong>What triggered this alert:</strong> {exp.get('trigger', '')}</p>
          <p><strong>Why it matters:</strong> {exp.get('why_it_matters', '')}</p>
          <p><strong>Suggested actions:</strong></p>
          <ul>{actions_html}</ul>
        </div>
        """
    except Exception:
        return ""


SEVERITY_COLOURS = {
    "Critical": "#dc3545",
    "High":     "#fd7e14",
    "Medium":   "#ffc107",
    "Low":      "#17a2b8",
}


def send_immediate_alert(alert: Alert, explanation: dict | None, actions: list[Action]):
    """Send an immediate email for a Critical or High alert."""
    colour = SEVERITY_COLOURS.get(alert.severity, "#6c757d")
    exp_json = json.dumps(explanation) if explanation else None

    subject = f"[{alert.severity}] Portfolio Alert — {alert.type.replace('_', ' ').title()}"

    body_html = f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:auto">
      <h2 style="color:{colour}">[{alert.severity}] {alert.type.replace('_', ' ').title()}</h2>
      <p style="color:#555">Asset: <strong>{alert.asset or 'Portfolio'}</strong> &nbsp;|&nbsp;
         {alert.timestamp.strftime('%Y-%m-%d %H:%M UTC')}</p>
      <p>{alert.message}</p>
      {_format_explanation(exp_json)}
      <h3>Recommended Actions</h3>
      {_format_actions(actions)}
      <hr style="margin-top:24px">
      <p style="color:#aaa;font-size:12px">Portfolio Alert & Regime Monitoring System</p>
    </body></html>
    """

    body_text = (
        f"[{alert.severity}] {alert.type}\n"
        f"Asset: {alert.asset or 'Portfolio'}\n"
        f"{alert.message}\n\n"
        + (f"Trigger: {explanation['trigger']}\n"
           f"Why it matters: {explanation['why_it_matters']}\n" if explanation else "")
        + "Actions:\n"
        + "\n".join(f"- {a.description}" for a in actions)
    )

    _send(subject, body_html, body_text)


def send_daily_digest(alerts: list[Alert]):
    """Send a daily digest email for Medium-severity alerts."""
    if not alerts:
        return

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    subject = f"Portfolio Daily Digest — {date_str} ({len(alerts)} alert{'s' if len(alerts) != 1 else ''})"

    rows = ""
    for alert in alerts:
        colour = SEVERITY_COLOURS.get(alert.severity, "#6c757d")
        rows += (
            f"<tr>"
            f"<td style='padding:6px;border-bottom:1px solid #eee'>"
            f"<span style='color:{colour};font-weight:bold'>{alert.severity}</span></td>"
            f"<td style='padding:6px;border-bottom:1px solid #eee'>{alert.asset or '—'}</td>"
            f"<td style='padding:6px;border-bottom:1px solid #eee'>{alert.message}</td>"
            f"</tr>"
        )

    body_html = f"""
    <html><body style="font-family:sans-serif;max-width:700px;margin:auto">
      <h2>Portfolio Daily Digest — {date_str}</h2>
      <p>{len(alerts)} medium-priority alert(s) requiring your attention:</p>
      <table style="width:100%;border-collapse:collapse">
        <thead><tr>
          <th style="text-align:left;padding:6px;background:#f1f1f1">Severity</th>
          <th style="text-align:left;padding:6px;background:#f1f1f1">Asset</th>
          <th style="text-align:left;padding:6px;background:#f1f1f1">Message</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="margin-top:16px">Log in to your dashboard for full details and actions.</p>
      <hr><p style="color:#aaa;font-size:12px">Portfolio Alert & Regime Monitoring System</p>
    </body></html>
    """

    body_text = f"Portfolio Daily Digest — {date_str}\n\n"
    for alert in alerts:
        body_text += f"[{alert.severity}] {alert.asset or 'Portfolio'}: {alert.message}\n"

    _send(subject, body_html, body_text)
