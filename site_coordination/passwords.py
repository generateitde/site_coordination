"""Password generation helpers."""

from __future__ import annotations

import secrets
import string


def generate_password(length: int = 16) -> str:
    """Generate a secure random password."""

    if length < 12:
        raise ValueError("Password length must be at least 12 characters.")
    alphabet = string.ascii_letters + string.digits + "!@#$%*_-"
    return "".join(secrets.choice(alphabet) for _ in range(length))
