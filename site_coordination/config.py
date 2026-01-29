"""Configuration helpers for the site coordination service."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class DatabaseConfig:
    """Database configuration."""

    path: Path


@dataclass(frozen=True)
class ImapConfig:
    """IMAP configuration."""

    host: str
    user: str
    password: str
    mailbox: str = "INBOX"


@dataclass(frozen=True)
class SmtpConfig:
    """SMTP configuration."""

    host: str
    user: str
    password: str
    port: int = 587
    sender_email: str = "wordpress@campus-rwth-aachen.com"


def load_database_config() -> DatabaseConfig:
    """Load database configuration from environment variables."""

    db_path = Path(os.environ.get("SITE_COORDINATION_DB", "site_coordination.sqlite"))
    return DatabaseConfig(path=db_path)


def load_imap_config() -> ImapConfig:
    """Load IMAP configuration from environment variables."""

    return ImapConfig(
        host=os.environ.get("SITE_COORDINATION_IMAP_HOST", ""),
        user=os.environ.get("SITE_COORDINATION_IMAP_USER", ""),
        password=os.environ.get("SITE_COORDINATION_IMAP_PASSWORD", ""),
        mailbox=os.environ.get("SITE_COORDINATION_IMAP_MAILBOX", "INBOX"),
    )


def load_smtp_config() -> SmtpConfig:
    """Load SMTP configuration from environment variables."""

    port = int(os.environ.get("SITE_COORDINATION_SMTP_PORT", "587"))
    return SmtpConfig(
        host=os.environ.get("SITE_COORDINATION_SMTP_HOST", ""),
        user=os.environ.get("SITE_COORDINATION_SMTP_USER", ""),
        password=os.environ.get("SITE_COORDINATION_SMTP_PASSWORD", ""),
        port=port,
        sender_email=os.environ.get(
            "SITE_COORDINATION_SENDER_EMAIL", "wordpress@campus-rwth-aachen.com"
        ),
    )
