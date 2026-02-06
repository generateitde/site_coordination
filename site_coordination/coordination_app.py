"""Web UI for site coordination workflows."""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import Iterable, Optional

from flask import Flask, flash, redirect, render_template, request, url_for
from jinja2 import ChoiceLoader, FileSystemLoader

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

from email_automation.service import on_send_email_click
from site_coordination import db
from site_coordination.config import load_smtp_config
from site_coordination.db_tools import get_connection
from site_coordination.email_parser import (
    EmailParseError,
    parse_access_request,
    parse_booking_request,
)
from site_coordination.notifications import (
    build_booking_confirmation_email,
    build_booking_denial_email,
    build_credentials_email,
    send_email,
)
from site_coordination.passwords import generate_password
from site_coordination.processor import handle_access_request, handle_booking_request


def create_app() -> Flask:
    """Create the Flask application."""

    base_dir = Path(__file__).resolve().parent
    templates_dir = base_dir / "templates_coordination"
    legacy_templates_dir = base_dir / "templates"
    app = Flask(
        __name__,
        template_folder=str(templates_dir),
        static_folder=str(base_dir / "static"),
    )
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(templates_dir)),
            FileSystemLoader(str(legacy_templates_dir)),
        ],
    )
    app.secret_key = os.environ.get("SITE_COORDINATION_SECRET", "dev-secret")
    _ensure_database()

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/registrations")
    def registrations() -> str:
        return render_template("registrations.html")

    @app.route("/registrations/manual", methods=["GET", "POST"])
    def registration_manual() -> str:
        if request.method == "POST":
            raw_email = request.form.get("raw_email", "")
            try:
                parsed = parse_access_request(raw_email)
                if _user_exists(parsed.email):
                    flash(
                        "A user with this email already exists. Registration not stored.",
                        "error",
                    )
                    return redirect(url_for("registration_manual"))
                with get_connection() as connection:
                    result = handle_access_request(connection, parsed)
                flash(result.message, "success")
                return redirect(url_for("registration_manual"))
            except EmailParseError as exc:
                flash(f"Could not parse registration email: {exc}", "error")
        return render_template("registration_manual.html")

    @app.route("/registrations/manage", methods=["GET", "POST"])
    def registrations_manage() -> str:
        if request.method == "POST":
            email = request.form.get("email", "")
            action = request.form.get("action", "")
            if email and action == "approve":
                _approve_registration(email)
            elif email and action == "deny":
                _deny_registration(email)
        query = request.args.get("q", "").strip()
        registrations = _fetch_registrations(query)
        status_labels = {
            "open": "Open",
            "offen": "Open",
            "registriert": "Registered",
            "denied": "Denied",
        }
        return render_template(
            "registrations_manage.html",
            registrations=registrations,
            query=query,
            status_labels=status_labels,
        )

    @app.route("/users/manage", methods=["GET", "POST"])
    def users_manage() -> str:
        selected_email = request.args.get("show_email", "").strip().lower()
        credentials_preview = None
        if selected_email:
            credentials_preview = _build_credentials_preview(selected_email)
        if request.method == "POST":
            email = request.form.get("email", "")
            action = request.form.get("action", "")
            if email and action == "send":
                _send_user_credentials(email)
        query = request.args.get("q", "").strip()
        users = _fetch_users(query)
        return render_template(
            "users_manage.html",
            users=users,
            query=query,
            credentials_preview=credentials_preview,
        )

    @app.get("/bookings")
    def bookings() -> str:
        return render_template("bookings.html")

    @app.route("/bookings/manual", methods=["GET", "POST"])
    def booking_manual() -> str:
        if request.method == "POST":
            raw_email = request.form.get("raw_email", "")
            try:
                parsed = parse_booking_request(raw_email)
                with get_connection() as connection:
                    result = handle_booking_request(connection, parsed)
                flash(result.message, "success")
                return redirect(url_for("booking_manual"))
            except EmailParseError as exc:
                flash(f"Could not parse booking email: {exc}", "error")
        return render_template("booking_manual.html")

    @app.route("/bookings/manage", methods=["GET", "POST"])
    def bookings_manage() -> str:
        booking_preview = None
        selected_booking_id = request.args.get("show_booking_id", "").strip()
        preview_action = request.args.get("preview_action", "").strip()
        if selected_booking_id:
            booking_preview = _build_booking_preview(selected_booking_id, preview_action)
        if request.method == "POST":
            booking_id = request.form.get("booking_id", "")
            action = request.form.get("action", "")
            send_response = request.form.get("send_response", "") == "yes"
            if booking_id and action == "approve":
                _approve_booking(int(booking_id))
                if send_response:
                    _send_booking_response(int(booking_id))
            elif booking_id and action == "deny":
                _deny_booking(int(booking_id))
                if send_response:
                    _send_booking_response(int(booking_id))
            elif booking_id and action == "send_response":
                _send_booking_response(int(booking_id))
        query = request.args.get("q", "").strip()
        bookings_list = _fetch_bookings(query)
        status_labels = {
            "pending_review": "Pending review",
            "zu_ueberpruefen": "Pending review",
            "gebucht": "Booked",
            "denied": "Denied",
        }
        return render_template(
            "bookings_manage.html",
            bookings=bookings_list,
            query=query,
            booking_preview=booking_preview,
            status_labels=status_labels,
        )

    @app.route("/activities", methods=["GET"])
    def activities() -> str:
        table = request.args.get("table", "research")
        query = request.args.get("q", "").strip()
        if table == "service":
            activity_rows = _fetch_activity_service(query)
        else:
            table = "research"
            activity_rows = _fetch_activity_research(query)
        return render_template(
            "activities.html",
            table=table,
            query=query,
            rows=activity_rows,
        )

    @app.route("/analysis", methods=["GET", "POST"])
    def analysis() -> str:
        selections = _analysis_selections()
        if request.method == "POST":
            email_filter = request.form.get("email", "").strip().lower()
            start_date = request.form.get("start_date") or None
            end_date = request.form.get("end_date") or None
            service_start = request.form.get("service_start_date") or None
            service_end = request.form.get("service_end_date") or None
        else:
            email_filter = ""
            start_date = None
            end_date = None
            service_start = None
            service_end = None
        booking_summary = _build_booking_summary(email_filter, start_date, end_date)
        user_activity = _build_user_activity_summary(email_filter, start_date, end_date)
        service_activity = _build_service_activity_summary(service_start, service_end)
        return render_template(
            "analysis.html",
            selections=selections,
            booking_summary=booking_summary,
            user_activity=user_activity,
            service_activity=service_activity,
            filters={
                "email": email_filter,
                "start_date": start_date,
                "end_date": end_date,
                "service_start_date": service_start,
                "service_end_date": service_end,
            },
        )

    return app


def _ensure_database() -> None:
    with get_connection() as connection:
        db.init_db(connection)
        db.ensure_users_credentials_column(connection)
        db.ensure_activity_research_name_columns(connection)


def _fetch_registrations(query: str) -> list[sqlite3.Row]:
    sql = "SELECT * FROM registrations"
    params: list[str] = []
    if query:
        sql += (
            " WHERE email LIKE ? OR first_name LIKE ? OR last_name LIKE ?"
            " OR affiliation LIKE ? OR project LIKE ? OR status LIKE ?"
        )
        like_query = f"%{query}%"
        params = [like_query] * 6
    sql += " ORDER BY created_at DESC"
    with get_connection() as connection:
        return connection.execute(sql, params).fetchall()


def _user_exists(email: str) -> bool:
    if not email:
        return False
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    return row is not None


def _fetch_bookings(query: str) -> list[sqlite3.Row]:
    sql = "SELECT * FROM bookings"
    params: list[str] = []
    if query:
        sql += (
            " WHERE email LIKE ? OR first_name LIKE ? OR last_name LIKE ?"
            " OR project LIKE ? OR timeslot_raw LIKE ? OR status LIKE ?"
        )
        like_query = f"%{query}%"
        params = [like_query] * 6
    sql += " ORDER BY created_at DESC"
    with get_connection() as connection:
        return connection.execute(sql, params).fetchall()


def _fetch_users(query: str) -> list[sqlite3.Row]:
    sql = "SELECT * FROM users"
    params: list[str] = []
    if query:
        sql += (
            " WHERE email LIKE ? OR first_name LIKE ? OR last_name LIKE ?"
            " OR affiliation LIKE ? OR project LIKE ? OR phone LIKE ?"
        )
        like_query = f"%{query}%"
        params = [like_query] * 6
    sql += " ORDER BY created_at DESC"
    with get_connection() as connection:
        return connection.execute(sql, params).fetchall()


def _fetch_activity_research(query: str) -> list[sqlite3.Row]:
    sql = "SELECT * FROM activity_research"
    params: list[str] = []
    if query:
        sql += (
            " WHERE email LIKE ? OR first_name LIKE ? OR last_name LIKE ?"
            " OR project LIKE ? OR presence LIKE ? OR created_at LIKE ?"
        )
        like_query, created_query = _activity_like_terms(query)
        params = [like_query] * 5 + [created_query]
    sql += " ORDER BY created_at DESC"
    with get_connection() as connection:
        return connection.execute(sql, params).fetchall()


def _fetch_activity_service(query: str) -> list[sqlite3.Row]:
    sql = "SELECT * FROM activity_service_provider"
    params: list[str] = []
    if query:
        sql += (
            " WHERE name LIKE ? OR company LIKE ? OR service LIKE ? OR presence LIKE ?"
            " OR created_at LIKE ?"
        )
        like_query, created_query = _activity_like_terms(query)
        params = [like_query] * 4 + [created_query]
    sql += " ORDER BY created_at DESC"
    with get_connection() as connection:
        return connection.execute(sql, params).fetchall()


def _activity_like_terms(query: str) -> tuple[str, str]:
    query = query.strip()
    if not query:
        return ("", "")
    like_query = f"%{query}%"
    normalized_date = _normalize_date_query(query)
    created_query = like_query
    if normalized_date and normalized_date != query:
        created_query = f"%{normalized_date}%"
    return like_query, created_query


def _normalize_date_query(query: str) -> str | None:
    parts = query.split(".")
    if len(parts) != 3:
        return None
    day, month, year = (part.strip() for part in parts)
    if not (day.isdigit() and month.isdigit() and year.isdigit()):
        return None
    if len(year) != 4:
        return None
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


def _approve_registration(email: str) -> None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM registrations WHERE email = ?",
            (email,),
        ).fetchone()
        if row is None:
            flash("Registration not found.", "error")
            return
        password = generate_password()
        db.insert_user(
            connection,
            email=row["email"],
            password=password,
            first_name=row["first_name"],
            last_name=row["last_name"],
            affiliation=row["affiliation"],
            project=row["project"],
            phone=row["phone"],
        )
        db.update_registration_status(connection, email, "registriert")
    flash(f"Registration approved and user created for {email}.", "success")


def _deny_registration(email: str) -> None:
    with get_connection() as connection:
        db.update_registration_status(connection, email, "denied")
    flash(f"Registration denied for {email}.", "success")


def _approve_booking(booking_id: int) -> None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM bookings WHERE id = ?",
            (booking_id,),
        ).fetchone()
        if row is None:
            flash("Booking not found.", "error")
            return
        connection.execute(
            "UPDATE bookings SET status = ? WHERE id = ?",
            ("gebucht", booking_id),
        )
        connection.commit()
    flash(f"Booking approved for {row['email']}.", "success")


def _deny_booking(booking_id: int) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE bookings SET status = ? WHERE id = ?",
            ("denied", booking_id),
        )
        connection.commit()
    flash("Booking denied.", "success")


def _send_credentials_email(email: str, password: str) -> bool:
    config = load_smtp_config()
    if not config.host:
        flash("SMTP host not configured; credentials email not sent.", "error")
        return False
    with get_connection() as connection:
        row = connection.execute(
            "SELECT first_name, last_name FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    if row is None:
        flash("User not found for credentials email.", "error")
        return False
    message = build_credentials_email(
        email,
        password,
        first_name=row["first_name"],
        last_name=row["last_name"],
    )
    send_email(config, message)
    return True


def _send_user_credentials(email: str) -> None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if row is None:
            flash("User not found.", "error")
            return
        password = row["password"]
    if _send_credentials_email(email, password):
        with get_connection() as connection:
            connection.execute(
                "UPDATE users SET credentials_sent = credentials_sent + 1 WHERE email = ?",
                (email,),
            )
            connection.commit()
        flash(f"Credentials sent to {email}.", "success")


def _build_credentials_preview(email: str) -> Optional[dict]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT email, password, first_name, last_name FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    if row is None:
        flash("User not found for credentials preview.", "error")
        return None
    message = build_credentials_email(
        row["email"],
        row["password"],
        first_name=row["first_name"],
        last_name=row["last_name"],
    )
    subject = message["Subject"] or ""
    body = message.get_content()
    return {"email": row["email"], "subject": subject, "body": body}


def _send_booking_email(email: str, row: sqlite3.Row, action: str) -> None:
    config = load_smtp_config()
    if not config.host:
        flash("SMTP host not configured; booking email not sent.", "error")
        return
    if action == "deny":
        message = build_booking_denial_email(email, row)
    else:
        message = build_booking_confirmation_email(email, row)
    send_email(config, message)


def _build_booking_preview(booking_id: str, action: str) -> Optional[dict]:
    if not booking_id.isdigit():
        flash("Booking not found for email preview.", "error")
        return None
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM bookings WHERE id = ?",
            (int(booking_id),),
        ).fetchone()
    if row is None:
        flash("Booking not found for email preview.", "error")
        return None
    resolved_action = action
    if not resolved_action:
        if row["status"] == "denied":
            resolved_action = "deny"
        elif row["status"] == "gebucht":
            resolved_action = "approve"
    if resolved_action not in {"approve", "deny"}:
        flash("Select an approved or denied booking to preview the email.", "error")
        return None
    if resolved_action == "deny":
        message = build_booking_denial_email(row["email"], row)
    else:
        message = build_booking_confirmation_email(row["email"], row)
    subject = message["Subject"] or ""
    body = message.get_content()
    return {
        "booking_id": row["id"],
        "email": row["email"],
        "subject": subject,
        "body": body,
    }


def _send_booking_response(booking_id: int) -> None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM bookings WHERE id = ?",
            (booking_id,),
        ).fetchone()
    if row is None:
        flash("Booking not found.", "error")
        return
    if row["status"] == "denied":
        action = "deny"
    elif row["status"] == "gebucht":
        action = "approve"
    else:
        flash("Booking must be approved or denied before sending a response.", "error")
        return
    try:
        on_send_email_click(booking_id)
    except Exception as exc:
        flash(f"Automated email failed: {exc}", "error")
        return
    flash(f"Automated email sent for booking {row['email']}.", "success")


def _analysis_selections() -> Iterable[str]:
    with get_connection() as connection:
        return db.fetch_user_emails(connection)


def _build_booking_summary(
    email_filter: str,
    start_date: Optional[str],
    end_date: Optional[str],
) -> dict:
    base_sql = "SELECT * FROM bookings WHERE 1=1"
    params: list[str] = []
    if email_filter:
        base_sql += " AND email = ?"
        params.append(email_filter)
    if start_date:
        base_sql += " AND date(created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        base_sql += " AND date(created_at) <= date(?)"
        params.append(end_date)
    with get_connection() as connection:
        rows = connection.execute(base_sql, params).fetchall()

    week_counts: dict[str, int] = {}
    week_projects: dict[str, dict[str, int]] = {}
    for row in rows:
        week = _extract_week(row["timeslot_raw"])
        week_counts[week] = week_counts.get(week, 0) + 1
        project = row["project"]
        week_projects.setdefault(week, {})
        week_projects[week][project] = week_projects[week].get(project, 0) + 1

    conflicts = {week: count for week, count in week_counts.items() if count > 1}
    return {
        "total": len(rows),
        "week_counts": week_counts,
        "week_projects": week_projects,
        "conflicts": conflicts,
    }


def _build_user_activity_summary(
    email_filter: str,
    start_date: Optional[str],
    end_date: Optional[str],
) -> dict:
    base_sql = "SELECT * FROM activity_research WHERE 1=1"
    params: list[str] = []
    if email_filter:
        base_sql += " AND email = ?"
        params.append(email_filter)
    if start_date:
        base_sql += " AND date(created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        base_sql += " AND date(created_at) <= date(?)"
        params.append(end_date)
    with get_connection() as connection:
        rows = connection.execute(base_sql, params).fetchall()
    per_user: dict[str, int] = {}
    for row in rows:
        per_user[row["email"]] = per_user.get(row["email"], 0) + 1
    return {"total": len(rows), "per_user": per_user}


def _build_service_activity_summary(
    start_date: Optional[str],
    end_date: Optional[str],
) -> dict:
    base_sql = "SELECT * FROM activity_service_provider WHERE 1=1"
    params: list[str] = []
    if start_date:
        base_sql += " AND date(created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        base_sql += " AND date(created_at) <= date(?)"
        params.append(end_date)
    with get_connection() as connection:
        rows = connection.execute(base_sql, params).fetchall()
    per_service: dict[str, int] = {}
    for row in rows:
        per_service[row["service"]] = per_service.get(row["service"], 0) + 1
    return {"total": len(rows), "per_service": per_service}


def _extract_week(timeslot_raw: str) -> str:
    if not timeslot_raw:
        return "unknown"
    parts = [part.strip() for part in timeslot_raw.split(";") if part.strip()]
    return parts[0] if parts else "unknown"


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
