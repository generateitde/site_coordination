"""Command line entrypoints for the site coordination service."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_database_config, load_imap_config, load_smtp_config
from . import db
from .email_parser import (
    EmailParseError,
    parse_access_request,
    parse_booking_request,
)
from .imap_watcher import fetch_unseen_messages
from .processor import handle_access_request, handle_booking_request
from .user_admin import approve_registration, reject_registration


def _handle_email_body(connection, body: str) -> str:
    if "BEGIN_ACCESS_REQUEST_V1" in body:
        request = parse_access_request(body)
        result = handle_access_request(connection, request)
        return result.message
    if "BEGIN_BOOKING_REQUEST_V1" in body:
        request = parse_booking_request(body)
        result = handle_booking_request(connection, request)
        return result.message
    raise EmailParseError("Unsupported email format.")


def _command_init_db(args: argparse.Namespace) -> None:
    config = load_database_config()
    connection = db.connect(config.path)
    db.init_db(connection)
    print(f"Database initialized at {config.path}")


def _command_process_file(args: argparse.Namespace) -> None:
    config = load_database_config()
    connection = db.connect(config.path)
    db.init_db(connection)
    body = Path(args.path).read_text(encoding="utf-8")
    message = _handle_email_body(connection, body)
    print(message)


def _command_process_imap(args: argparse.Namespace) -> None:
    config = load_database_config()
    imap_config = load_imap_config()
    connection = db.connect(config.path)
    db.init_db(connection)

    messages = fetch_unseen_messages(imap_config)
    for message in messages:
        try:
            result = _handle_email_body(connection, message.body)
            print(f"Processed: {message.subject} -> {result}")
        except EmailParseError as exc:
            print(f"Skipped: {message.subject} ({exc})")


def _command_approve(args: argparse.Namespace) -> None:
    config = load_database_config()
    smtp_config = load_smtp_config()
    connection = db.connect(config.path)
    db.init_db(connection)
    result = approve_registration(connection, smtp_config, args.email)
    print(f"Registration {result.email} updated: {result.status}")


def _command_reject(args: argparse.Namespace) -> None:
    config = load_database_config()
    connection = db.connect(config.path)
    db.init_db(connection)
    result = reject_registration(connection, args.email)
    print(f"Registration {result.email} updated: {result.status}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Site coordination service.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db_parser = subparsers.add_parser("init-db", help="Initialize database")
    init_db_parser.set_defaults(func=_command_init_db)

    process_file_parser = subparsers.add_parser(
        "process-file", help="Process an email body from a file"
    )
    process_file_parser.add_argument("path", help="Path to email body text file")
    process_file_parser.set_defaults(func=_command_process_file)

    process_imap_parser = subparsers.add_parser(
        "process-imap", help="Process unseen emails from IMAP"
    )
    process_imap_parser.set_defaults(func=_command_process_imap)

    approve_parser = subparsers.add_parser(
        "approve", help="Approve a registration and send credentials"
    )
    approve_parser.add_argument("email", help="Email to approve")
    approve_parser.set_defaults(func=_command_approve)

    reject_parser = subparsers.add_parser("reject", help="Reject a registration")
    reject_parser.add_argument("email", help="Email to reject")
    reject_parser.set_defaults(func=_command_reject)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
