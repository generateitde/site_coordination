"""Shared database helpers for web apps."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from site_coordination.config import load_database_config


def get_connection() -> sqlite3.Connection:
    """Return a configured SQLite connection."""

    config = load_database_config()
    db_path = Path(config.path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection
