"""HTTP client for Power Automate email flow."""

from __future__ import annotations

from typing import Mapping

import requests

from email_automation.config import FLOW_URL


def trigger_flow_send_email(payload: Mapping[str, str], timeout: int = 10) -> None:
    """Invoke the Power Automate HTTP trigger to send an email."""
    response = requests.post(FLOW_URL, json=payload, timeout=timeout)
    if response.status_code not in {200, 202}:
        raise RuntimeError(
            f"Power Automate flow failed with status {response.status_code}: {response.text}"
        )
