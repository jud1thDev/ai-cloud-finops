"""Slack integration for FinOps AI alerts.

Converts AI output alerts[] to Slack Block Kit format and posts via webhook.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List

from finops_study.config import SLACK_WEBHOOK_URL

# Urgency → Slack emoji mapping
_URGENCY_EMOJI = {
    "info": ":information_source:",
    "warning": ":warning:",
    "critical": ":rotating_light:",
}

# Severity → color mapping
_SEVERITY_COLOR = {
    "low": "#36a64f",
    "medium": "#daa038",
    "high": "#e01e5a",
    "critical": "#ff0000",
}


def _alert_to_block(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single alert to a Slack Block Kit attachment."""
    urgency = alert.get("urgency", "info")
    severity = alert.get("severity", "medium")
    emoji = _URGENCY_EMOJI.get(urgency, ":grey_question:")
    color = _SEVERITY_COLOR.get(severity, "#cccccc")

    return {
        "color": color,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {alert.get('title', 'Alert')}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert.get("message", ""),
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Channel:* {alert.get('channel', 'N/A')} | *Severity:* {severity} | *Urgency:* {urgency}",
                    }
                ],
            },
        ],
    }


def send_alerts(
    alerts: List[Dict[str, Any]],
    scenario_id: str = "",
    username: str = "",
    webhook_url: str = "",
) -> bool:
    """Post alerts to Slack via webhook.

    Returns True on success, False on failure.
    """
    url = webhook_url or SLACK_WEBHOOK_URL
    if not url:
        return False

    if not alerts:
        return True

    attachments = [_alert_to_block(a) for a in alerts]

    payload = {
        "text": f"FinOps Alert — {scenario_id} by {username}",
        "attachments": attachments,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status == 200
    except urllib.error.URLError:
        return False
