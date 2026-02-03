"""Configuration helpers for the site coordination service."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict


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


def _load_env_file(env_path: Path) -> Dict[str, str]:
    """Load key=value lines from a .env file."""

    if not env_path.exists():
        return {}
    data: Dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _apply_env_overrides(values: Dict[str, str]) -> None:
    """Apply .env values to os.environ if not already set."""

    for key, value in values.items():
        os.environ.setdefault(key, value)


def load_env() -> None:
    """Load .env file from the project root if present."""

    env_path = Path(os.environ.get("SITE_COORDINATION_ENV", ".env"))
    _apply_env_overrides(_load_env_file(env_path))


def load_database_config() -> DatabaseConfig:
    """Load database configuration from environment variables."""

    load_env()
    base_dir = Path.cwd()
    db_value = os.environ.get("SITE_COORDINATION_DB", "site_coordination.sqlite")
    db_path = Path(db_value)
    if not db_path.is_absolute():
        db_path = (base_dir / db_path).resolve()
    return DatabaseConfig(path=db_path)


def load_imap_config() -> ImapConfig:
    """Load IMAP configuration from environment variables."""

    load_env()
    return ImapConfig(
        host=os.environ.get("SITE_COORDINATION_IMAP_HOST", ""),
        user=os.environ.get("SITE_COORDINATION_IMAP_USER", ""),
        password=os.environ.get("SITE_COORDINATION_IMAP_PASSWORD", ""),
        mailbox=os.environ.get("SITE_COORDINATION_IMAP_MAILBOX", "INBOX"),
    )


def load_smtp_config() -> SmtpConfig:
    """Load SMTP configuration from environment variables."""

    load_env()
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
