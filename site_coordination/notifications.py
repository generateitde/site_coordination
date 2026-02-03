"""Notification helpers for account provisioning."""

from __future__ import annotations

from email.message import EmailMessage
import smtplib
from typing import Mapping

from .config import SmtpConfig


def build_credentials_email(recipient: str, password: str) -> EmailMessage:
    """Build an email message containing user credentials."""

    message = EmailMessage()
    message["Subject"] = "Your Research Platform Account"
    message["To"] = recipient
    message.set_content(
        "\n".join(
            [
                "Hello,",
                "",
                "your registration was approved. Here are your credentials:",
                f"Email: {recipient}",
                f"Password: {password}",
                "",
                "Please keep this information secure.",
                "",
                "How to book a timeslot:",
                "1) Log into the booking page.",
                "2) Choose your timeslot and project details.",
                "3) Submit the form to request approval.",
                "",
                "Best regards,",
                "Site Coordination Team",
            ]
        )
    )
    return message


def build_booking_confirmation_email(recipient: str, booking: Mapping[str, str]) -> EmailMessage:
    """Build an email message confirming a booking."""

    message = EmailMessage()
    message["Subject"] = "Your Booking Confirmation"
    message["To"] = recipient
    message.set_content(
        "\n".join(
            [
                "Hello,",
                "",
                "your booking request has been approved.",
                f"Project: {booking.get('project', '')}",
                f"Timeslot: {booking.get('timeslot_raw', '')}",
                f"Duration (weeks): {booking.get('duration_weeks', '')}",
                "",
                "Please ensure you have your login credentials ready on the day of your visit",
                "to enter the Reference Construction Site in Aachen.",
                "",
                "Best regards,",
                "Site Coordination Team",
            ]
        )
    )
    return message


def send_email(config: SmtpConfig, message: EmailMessage) -> None:
    """Send an email via SMTP."""

    message["From"] = config.sender_email
    with smtplib.SMTP(config.host, config.port) as server:
        server.starttls()
        if config.user:
            server.login(config.user, config.password)
        server.send_message(message)
