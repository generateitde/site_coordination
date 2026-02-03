"""Database access helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable


@dataclass(frozen=True)
class RegistrationRecord:
    email: str
    first_name: str
    last_name: str
    affiliation: str
    project: str
    phone: str
    activity: str
    status: str


@dataclass(frozen=True)
class BookingRecord:
    email: str
    first_name: str
    last_name: str
    project: str
    timeslot_raw: str
    duration_weeks: str
    indoor: str
    outdoor: str
    outdoor_type: str
    equipment: str
    status: str


def connect(db_path: Path) -> sqlite3.Connection:
    """Connect to the SQLite database."""

    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    """Create the required tables if they do not exist."""

    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS registrations (
            email TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            affiliation TEXT NOT NULL,
            project TEXT NOT NULL,
            phone TEXT NOT NULL,
            activity TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            affiliation TEXT NOT NULL,
            project TEXT NOT NULL,
            phone TEXT NOT NULL,
            credentials_sent INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            project TEXT NOT NULL,
            timeslot_raw TEXT NOT NULL,
            duration_weeks TEXT NOT NULL,
            indoor TEXT NOT NULL,
            outdoor TEXT NOT NULL,
            outdoor_type TEXT NOT NULL,
            equipment TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES users(email)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_research (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            project TEXT NOT NULL,
            presence TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES users(email)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_service_provider (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT NOT NULL,
            mobile TEXT NOT NULL,
            service TEXT NOT NULL,
            presence TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()


def ensure_users_credentials_column(connection: sqlite3.Connection) -> None:
    """Ensure users table has the credentials_sent column."""

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(users)").fetchall()
    }
    if "credentials_sent" not in columns:
        connection.execute(
            "ALTER TABLE users ADD COLUMN credentials_sent INTEGER NOT NULL DEFAULT 0"
        )
        connection.commit()


def insert_registration(connection: sqlite3.Connection, record: RegistrationRecord) -> None:
    """Insert a registration record."""

    connection.execute(
        """
        INSERT OR REPLACE INTO registrations (
            email, first_name, last_name, affiliation, project, phone, activity, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.email,
            record.first_name,
            record.last_name,
            record.affiliation,
            record.project,
            record.phone,
            record.activity,
            record.status,
        ),
    )
    connection.commit()


def update_registration_status(
    connection: sqlite3.Connection, email: str, status: str
) -> None:
    """Update the registration status."""

    connection.execute(
        "UPDATE registrations SET status = ? WHERE email = ?",
        (status, email),
    )
    connection.commit()


def insert_user(
    connection: sqlite3.Connection,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    affiliation: str,
    project: str,
    phone: str,
) -> None:
    """Insert a user record."""

    connection.execute(
        """
        INSERT OR REPLACE INTO users (
            email, password, first_name, last_name, affiliation, project, phone
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (email, password, first_name, last_name, affiliation, project, phone),
    )
    connection.commit()


def insert_booking(connection: sqlite3.Connection, record: BookingRecord) -> None:
    """Insert a booking record."""

    connection.execute(
        """
        INSERT INTO bookings (
            email, first_name, last_name, project, timeslot_raw, duration_weeks,
            indoor, outdoor, outdoor_type, equipment, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.email,
            record.first_name,
            record.last_name,
            record.project,
            record.timeslot_raw,
            record.duration_weeks,
            record.indoor,
            record.outdoor,
            record.outdoor_type,
            record.equipment,
            record.status,
        ),
    )
    connection.commit()


def fetch_user_emails(connection: sqlite3.Connection) -> Iterable[str]:
    """Fetch all registered user emails."""

    cursor = connection.execute("SELECT email FROM users")
    return [row["email"] for row in cursor.fetchall()]
