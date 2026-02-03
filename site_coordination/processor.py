"""Workflow processor for incoming emails."""

from __future__ import annotations

from dataclasses import dataclass

from . import db
from .email_parser import AccessRequest, BookingRequest


@dataclass(frozen=True)
class ProcessingResult:
    message: str


def handle_access_request(connection, request: AccessRequest) -> ProcessingResult:
    """Store an access request with status 'open'."""

    record = db.RegistrationRecord(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        affiliation=request.affiliation,
        project=request.project,
        phone=request.phone,
        activity=request.activity,
        status="open",
    )
    db.insert_registration(connection, record)
    return ProcessingResult(message=f"Registration stored for {request.email}.")


def handle_booking_request(connection, request: BookingRequest) -> ProcessingResult:
    """Store a booking request with status 'pending_review'."""

    record = db.BookingRecord(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        project=request.project,
        timeslot_raw=request.timeslot_raw,
        duration_weeks=request.duration_weeks,
        indoor=request.indoor,
        outdoor=request.outdoor,
        outdoor_type=request.outdoor_type,
        equipment=request.equipment,
        status="pending_review",
    )
    db.insert_booking(connection, record)
    return ProcessingResult(message=f"Booking stored for {request.email}.")
