"""Service layer for sending automated emails via Power Automate."""

from __future__ import annotations

from typing import Dict

from email_automation.config import load_settings
from email_automation.mailer import trigger_flow_send_email


def build_email_from_db(order_id: int) -> Dict[str, str]:
    """Stub to build email content from a database record."""
    return {
        "to": "recipient@example.com",
        "subject": f"Order update #{order_id}",
        "body": (
            "Dies ist ein Platzhalter für den E-Mail-Text. "
            "Hier soll später der Inhalt aus der Datenbank eingefügt werden."
        ),
        "contentType": "text",
    }


def on_send_email_click(order_id: int) -> None:
    """Handle UI button click to send an automated email."""
    settings = load_settings()
    email_payload = build_email_from_db(order_id)
    payload = {
        "token": settings.flow_secret,
        "to": email_payload["to"],
        "subject": email_payload["subject"],
        "body": email_payload["body"],
        "contentType": email_payload["contentType"],
    }
    trigger_flow_send_email(payload)
