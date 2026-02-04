"""Notification helpers for account provisioning."""

from __future__ import annotations

from email.message import EmailMessage
import smtplib
from typing import Mapping

from .config import SmtpConfig


def build_credentials_email(
    recipient: str,
    password: str,
    first_name: str,
    last_name: str,
) -> EmailMessage:
    """Build an email message containing user credentials."""

    message = EmailMessage()
    message["Subject"] = (
        "Your registration for the Reference Construction Site has been approved"
    )
    message["To"] = recipient
    full_name = " ".join(part for part in [first_name, last_name] if part).strip()
    greeting_name = full_name or "there"
    message.set_content(
        "\n".join(
            [
                f"Dear {greeting_name},",
                "",
                "your registration has been approved.",
                "",
                "Below are your credentials for Check-In and Check-Out at the Reference Construction Site in Aachen.",
                "",
                f"Email: {recipient}",
                f"Password: {password}",
                "",
                "Please keep this information secure.",
                "",
                "How to book a timeslot:",
                "",
                "Log in to the booking page",
                "https://construction-robotics.de/en/referencesite/members-area/booking/",
                "Use the Members Area password: CARE_DFG_2026",
                "",
                "1) Enter your first name and last name",
                "2) Enter the same email address as in this message",
                "3) Enter the project you are working on",
                "4) Select your requested timeslot",
                "--> Choose the starting week",
                "--> Choose the duration in weeks",
                "",
                "Complete all required fields",
                "",
                "Submit the form",
                "Your request will be reviewed for approval",
                "",
                "Best regards,",
                "",
                "CCR Reference Construction Site Coordination Team",
            ]
        )
    )
    return message


def _booking_value(booking: Mapping[str, str], key: str) -> str:
    if hasattr(booking, "get"):
        return booking.get(key, "")
    if key in booking.keys():
        return booking[key]
    return ""


def build_booking_confirmation_email(recipient: str, booking: Mapping[str, str]) -> EmailMessage:
    """Build an email message confirming a booking."""

    message = EmailMessage()
    message["Subject"] = (
        "Your booking at the Reference Construction Site has been confirmed"
    )
    message["To"] = recipient
    full_name = " ".join(
        part
        for part in [
            _booking_value(booking, "first_name"),
            _booking_value(booking, "last_name"),
        ]
        if part
    ).strip()
    greeting_name = full_name or "there"
    message.set_content(
        "\n".join(
            [
                f"Dear {greeting_name},",
                "",
                "your booking has been successfully approved.",
                "",
                "Below are the details of your confirmed timeslot at the Reference Construction Site in Aachen.",
                "",
                f"Project: {_booking_value(booking, 'project')}",
                f"Timeslot: {_booking_value(booking, 'timeslot_raw')}",
                f"Duration: {_booking_value(booking, 'duration_weeks')}",
                "",
                "Please arrive on site according to your booked start date.",
                "",
                "Check-In and Check-Out are mandatory.",
                "Use your personal login credentials for this purpose.",
                "",
                "If any details are incorrect or your plans change, please contact the site coordination team in advance.",
                "",
                "Entrance location:",
                "https://w3w.co/marginal.speaker.kingdom",
                "",
                "Official address:",
                "Maria-Lipp-Straße 1",
                "52074 Aachen",
                "",
                "Best regards,",
                "Reference Construction Site Coordination Team",
            ]
        )
    )
    return message


def build_booking_denial_email(recipient: str, booking: Mapping[str, str]) -> EmailMessage:
    """Build an email message denying a booking."""

    message = EmailMessage()
    message["Subject"] = (
        "Your booking request at the Reference Construction Site was not approved"
    )
    message["To"] = recipient
    full_name = " ".join(
        part
        for part in [
            _booking_value(booking, "first_name"),
            _booking_value(booking, "last_name"),
        ]
        if part
    ).strip()
    greeting_name = full_name or "there"
    message.set_content(
        "\n".join(
            [
                f"Dear {greeting_name},",
                "",
                "your booking request for the Reference Construction Site in Aachen could not be approved.",
                "",
                "The requested timeslot is currently unavailable or conflicts with existing bookings or site constraints.",
                "",
                "No booking has been created for this request.",
                "",
                "You may submit a new booking request with an alternative timeslot.",
                "",
                "If you have questions regarding availability or requirements, please contact the site coordination team before submitting a new request.",
                "",
                "Best regards,",
                "Reference Construction Site Coordination Team",
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
