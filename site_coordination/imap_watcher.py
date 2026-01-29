"""IMAP polling utilities to read WordPress form emails."""

from __future__ import annotations

from dataclasses import dataclass
from email.message import Message
from email.parser import BytesParser
from email.policy import default
import imaplib

from .config import ImapConfig


@dataclass(frozen=True)
class InboxMessage:
    subject: str
    body: str
    raw: Message


def _extract_body(message: Message) -> str:
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                return part.get_content()
    return message.get_content()


def fetch_unseen_messages(config: ImapConfig) -> list[InboxMessage]:
    """Fetch unseen messages from IMAP."""

    messages: list[InboxMessage] = []
    with imaplib.IMAP4_SSL(config.host) as client:
        client.login(config.user, config.password)
        client.select(config.mailbox)
        status, data = client.search(None, "UNSEEN")
        if status != "OK":
            return messages
        for msg_id in data[0].split():
            fetch_status, msg_data = client.fetch(msg_id, "(RFC822)")
            if fetch_status != "OK":
                continue
            msg_bytes = msg_data[0][1]
            parsed = BytesParser(policy=default).parsebytes(msg_bytes)
            messages.append(
                InboxMessage(
                    subject=parsed.get("Subject", ""),
                    body=_extract_body(parsed),
                    raw=parsed,
                )
            )
            client.store(msg_id, "+FLAGS", "\\Seen")
    return messages
