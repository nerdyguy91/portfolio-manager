"""
Explanation Engine.

Calls the Claude API to generate a plain-language explanation for a Critical or High alert.
Validates the output against explanation.schema.json.
Updates the alert record with the explanation.
Flags for human review if confidence < 0.75.
"""

import json
import os
from pathlib import Path
import anthropic
import jsonschema
from dotenv import load_dotenv
from tools.db import update_alert_explanation, Alert

load_dotenv()

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "explanation.schema.json"
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "explanation_engine.md"
CONFIDENCE_THRESHOLD = 0.75
MODEL = "claude-sonnet-4-6"


def _load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text()


def _build_user_message(alert: Alert, context: dict, regime: str) -> str:
    return json.dumps({
        "alert": {
            "type": alert.type,
            "severity": alert.severity,
            "asset": alert.asset,
            "message": alert.message,
        },
        "data_context": context,
        "regime_state": regime,
    }, indent=2)


def generate_explanation(alert: Alert, context: dict, regime: str) -> dict | None:
    """
    Generate and persist an explanation for the given alert.

    Returns the validated explanation dict, or None if generation fails.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set in environment.")

    schema = _load_schema()
    system_prompt = _load_system_prompt()
    user_message = _build_user_message(alert, context, regime)

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        explanation = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[explanation_tool] JSON parse error: {e}\nRaw output:\n{raw}")
        return None

    try:
        jsonschema.validate(instance=explanation, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"[explanation_tool] Schema validation failed: {e.message}")
        return None

    needs_review = explanation["confidence"] < CONFIDENCE_THRESHOLD
    update_alert_explanation(
        alert_id=alert.id,
        explanation=json.dumps(explanation),
        needs_review=needs_review,
    )

    if needs_review:
        print(f"[explanation_tool] Alert {alert.id} flagged for human review "
              f"(confidence={explanation['confidence']:.2f})")

    return explanation
