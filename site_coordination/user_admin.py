"""Admin actions for approving registrations."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from . import db
from .notifications import build_credentials_email, send_email
from .passwords import generate_password
from .config import SmtpConfig


@dataclass(frozen=True)
class ApprovalResult:
    email: str
    status: str


def approve_registration(
    connection: sqlite3.Connection, smtp_config: SmtpConfig, email: str
) -> ApprovalResult:
    """Approve a registration and create a user account."""

    cursor = connection.execute(
        "SELECT * FROM registrations WHERE email = ?",
        (email,),
    )
    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Registration not found for {email}.")

    password = generate_password()
    db.insert_user(
        connection,
        email=row["email"],
        password=password,
        first_name=row["first_name"],
        last_name=row["last_name"],
        affiliation=row["affiliation"],
        project=row["project"],
        phone=row["phone"],
    )
    db.update_registration_status(connection, email, "erfolgreich")

    message = build_credentials_email(email, password)
    send_email(smtp_config, message)

    return ApprovalResult(email=email, status="erfolgreich")


def reject_registration(connection: sqlite3.Connection, email: str) -> ApprovalResult:
    """Reject a registration."""

    db.update_registration_status(connection, email, "abgelehnt")
    return ApprovalResult(email=email, status="abgelehnt")
