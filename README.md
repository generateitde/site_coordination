# site_coordination

Automation of construction site access.

## Overview

This repository provides a Python-based foundation for the WordPress form workflow described in your
requirements. It focuses on:

- **Parsing WordPress form emails** for registrations and booking requests.
- **Persisting data in SQLite** with clear separation between registrations, users, bookings, and
  activity logs.
- **Administrative approval flow** that generates secure passwords and notifies the registrant by email.
- **IMAP polling** to automatically read new form emails.

The system is designed to be extended with a web UI for check-in/check-out and analytics dashboards.

## Database Tables

- `registrations`: stores incoming registration requests with status `offen`, `erfolgreich`, or `abgelehnt`.
- `users`: stores verified user accounts (email + generated password + profile data).
- `bookings`: stores booking requests with status `zu_ueberpruefen`.
- `activity_research`: stores check-in/check-out actions for registered researchers.
- `activity_service_provider`: stores check-in/check-out actions for service providers.

## Email Formats Supported

### Registration (ACCESS_REQUEST v1)

```
BEGIN_ACCESS_REQUEST_V1
first_name=[first-name]
last_name=[last-name]
email=[email]
affiliation=[affiliation]
project=[project]
phone=[phone]
activity_begin
[activity]
activity_end
END_ACCESS_REQUEST_V1
```

### Booking (BOOKING_REQUEST v1)

```
BEGIN_BOOKING_REQUEST_V1
first_name=[first-name]
last_name=[last-name]
email=[email]
project=[project]

timeslot_raw=[timeslot]
duration_weeks=[duration_weeks]

indoor=[indoor]
outdoor=[outdoor]
outdoor_type=[outdoor_type]
equipment=[equipment]
END_BOOKING_REQUEST_V1
```

## Quickstart

1. Initialize the database:

```
python -m site_coordination.cli init-db
```

2. Process a single email body from a file:

```
python -m site_coordination.cli process-file path/to/email.txt
```

3. Process unseen emails from IMAP:

```
export SITE_COORDINATION_IMAP_HOST=imap.example.com
export SITE_COORDINATION_IMAP_USER=wordpress@example.com
export SITE_COORDINATION_IMAP_PASSWORD=secret
python -m site_coordination.cli process-imap
```

4. Approve a registration and send credentials:

```
export SITE_COORDINATION_SMTP_HOST=smtp.example.com
export SITE_COORDINATION_SMTP_USER=wordpress@example.com
export SITE_COORDINATION_SMTP_PASSWORD=secret
python -m site_coordination.cli approve user@example.com
```

5. Reject a registration:

```
python -m site_coordination.cli reject user@example.com
```

## Environment Variables

- `SITE_COORDINATION_DB`: SQLite path (default: `site_coordination.sqlite`).
- `SITE_COORDINATION_IMAP_HOST`, `SITE_COORDINATION_IMAP_USER`, `SITE_COORDINATION_IMAP_PASSWORD`,
  `SITE_COORDINATION_IMAP_MAILBOX`.
- `SITE_COORDINATION_SMTP_HOST`, `SITE_COORDINATION_SMTP_USER`, `SITE_COORDINATION_SMTP_PASSWORD`,
  `SITE_COORDINATION_SMTP_PORT`, `SITE_COORDINATION_SENDER_EMAIL`.

> **Note:** Update the credentials in the `.env` file before using the IMAP/SMTP workflows.

## Next Steps

- Add a web UI for check-in/check-out (QR entry).
- Add analytics scripts for booking conflict detection and per-user activity reports.
- Extend the email templates and translation for German UI.
