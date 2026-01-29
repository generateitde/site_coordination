"""Email parsing for WordPress form submissions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

ACCESS_REQUEST_MARKER = "BEGIN_ACCESS_REQUEST_V1"
ACCESS_REQUEST_END = "END_ACCESS_REQUEST_V1"
BOOKING_REQUEST_MARKER = "BEGIN_BOOKING_REQUEST_V1"
BOOKING_REQUEST_END = "END_BOOKING_REQUEST_V1"


class EmailParseError(ValueError):
    """Raised when an email cannot be parsed."""


@dataclass(frozen=True)
class AccessRequest:
    first_name: str
    last_name: str
    email: str
    affiliation: str
    project: str
    phone: str
    activity: str


@dataclass(frozen=True)
class BookingRequest:
    first_name: str
    last_name: str
    email: str
    project: str
    timeslot_raw: str
    duration_weeks: str
    indoor: str
    outdoor: str
    outdoor_type: str
    equipment: str


def _parse_key_values(lines: list[str]) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for line in lines:
        if not line.strip():
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def parse_access_request(body: str) -> AccessRequest:
    """Parse an access request email body."""

    if ACCESS_REQUEST_MARKER not in body:
        raise EmailParseError("Missing access request marker.")

    start_index = body.index(ACCESS_REQUEST_MARKER) + len(ACCESS_REQUEST_MARKER)
    end_index = body.index(ACCESS_REQUEST_END)
    payload = body[start_index:end_index].strip()
    lines = payload.splitlines()

    activity_start: Optional[int] = None
    activity_end: Optional[int] = None
    for idx, line in enumerate(lines):
        if line.strip() == "activity_begin":
            activity_start = idx + 1
        if line.strip() == "activity_end":
            activity_end = idx
            break

    activity = ""
    if activity_start is not None and activity_end is not None:
        activity = "\n".join(lines[activity_start:activity_end]).strip()
        filtered_lines = lines[:activity_start - 1] + lines[activity_end + 1 :]
    else:
        filtered_lines = lines

    data = _parse_key_values(filtered_lines)
    required = [
        "first_name",
        "last_name",
        "email",
        "affiliation",
        "project",
        "phone",
    ]
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise EmailParseError(f"Missing required fields: {', '.join(missing)}")

    return AccessRequest(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        affiliation=data["affiliation"],
        project=data["project"],
        phone=data["phone"],
        activity=activity,
    )


def parse_booking_request(body: str) -> BookingRequest:
    """Parse a booking request email body."""

    if BOOKING_REQUEST_MARKER not in body:
        raise EmailParseError("Missing booking request marker.")

    start_index = body.index(BOOKING_REQUEST_MARKER) + len(BOOKING_REQUEST_MARKER)
    end_index = body.index(BOOKING_REQUEST_END)
    payload = body[start_index:end_index].strip()
    data = _parse_key_values(payload.splitlines())

    required = [
        "first_name",
        "last_name",
        "email",
        "project",
        "timeslot_raw",
        "duration_weeks",
        "indoor",
        "outdoor",
        "outdoor_type",
        "equipment",
    ]
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise EmailParseError(f"Missing required fields: {', '.join(missing)}")

    return BookingRequest(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        project=data["project"],
        timeslot_raw=data["timeslot_raw"],
        duration_weeks=data["duration_weeks"],
        indoor=data["indoor"],
        outdoor=data["outdoor"],
        outdoor_type=data["outdoor_type"],
        equipment=data["equipment"],
    )
