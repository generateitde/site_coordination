"""Simple web UI for site coordination check-in/out."""

from __future__ import annotations

import os
import base64
import importlib
import importlib.util
import io
import socket
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus


from site_coordination import db
from site_coordination.db_tools import get_connection


def create_app() -> Flask:
    """Create the Flask application."""

    base_dir = Path(__file__).resolve().parent
    _ensure_database()
    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates_checkin"),
        static_folder=str(base_dir / "static"),
    )
    app.secret_key = os.environ.get("SITE_COORDINATION_SECRET", "dev-secret")

    @app.get("/")
    def index() -> str:
        base_url = _get_base_url(request.host_url)
        base_url = base_url.strip()
        if not base_url.endswith("/"):
            base_url = f"{base_url}/"
        qr_code_data_uri = _build_qr_code_data_uri(base_url)
        qr_download_url = url_for("qr_code_png")
        return render_template(
            "index.html",
            base_url=base_url,
            qr_code_data_uri=qr_code_data_uri,
            qr_download_url=qr_download_url,
        )

    @app.post("/select")
    def select_role():
        role = request.form.get("role")
        if role == "researcher":
            return redirect(url_for("login"))
        return redirect(url_for("service_provider"))

    @app.get("/service-provider")
    def service_provider() -> str:
        return render_template("service_provider.html")

    @app.get("/registrations")
    def registrations() -> str:
        return render_template("registrations.html")

    @app.get("/bookings")
    def bookings() -> str:
        return render_template("bookings.html")

    @app.get("/qr.png")
    def qr_code_png() -> Response:
        base_url = _get_base_url(request.host_url)
        base_url = base_url.strip()
        if not base_url.endswith("/"):
            base_url = f"{base_url}/"
        qr_data = _build_qr_code_data_uri(base_url)
        if not qr_data:
            return Response(
                "QR code generation requires qrcode[pil]. Install dependencies and retry.",
                status=503,
                mimetype="text/plain",
            )
        image_bytes = base64.b64decode(qr_data.split(",", 1)[1])
        return send_file(
            io.BytesIO(image_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name="checkin-qr.png",
        )

    @app.route("/login", methods=["GET", "POST"])
    def login() -> str:
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()
            user = _fetch_user(email)
            if user is None or password != user[0]:
                flash("Falsche Login-Daten. Bitte erneut versuchen.", "error")
            else:
                session["user_email"] = email
                session["user_project"] = user[1]
                session["user_first_name"] = user[2]
                session["user_last_name"] = user[3]
                return redirect(url_for("checkin"))
        return render_template("login.html")

    @app.route("/checkin", methods=["GET", "POST"])
    def checkin() -> str:
        if "user_email" not in session:
            return redirect(url_for("login"))
        email = session["user_email"]
        first_name = session.get("user_first_name", "")
        last_name = session.get("user_last_name", "")
        projects = _fetch_booking_projects(email)
        fallback_project = session.get("user_project", "")
        if not projects and fallback_project:
            projects = [fallback_project]
        selected_project = session.get("selected_project")
        if selected_project not in projects:
            selected_project = projects[0] if projects else ""
        if request.method == "POST":
            presence = request.form.get("presence")
            submitted_project = request.form.get("project", "")
            if submitted_project in projects:
                selected_project = submitted_project
            elif submitted_project and not projects:
                selected_project = submitted_project
            if not selected_project:
                flash("Bitte ein Projekt auswählen.", "error")
            elif presence in {"check-in", "check-out"}:
                _insert_activity(email, first_name, last_name, selected_project, presence)
                session["selected_project"] = selected_project
                flash("Eintrag gespeichert.", "success")
            else:
                flash("Bitte eine gültige Auswahl treffen.", "error")
        return render_template(
            "checkin.html",
            email=email,
            project=selected_project,
            projects=projects,
        )

    @app.get("/logout")
    def logout() -> str:
        session.clear()
        return redirect(url_for("index"))

    return app


def _fetch_user(email: str) -> Optional[Tuple[str, str, str, str]]:
    if not email:
        return None
    with get_connection() as connection:
        row = connection.execute(
            "SELECT password, project, first_name, last_name FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    if row is None:
        return None
    return row["password"], row["project"], row["first_name"], row["last_name"]


def _fetch_booking_projects(email: str) -> list[str]:
    if not email:
        return []
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT DISTINCT project FROM bookings WHERE email = ? ORDER BY project",
            (email,),
        ).fetchall()
    return [row["project"] for row in rows]


def _insert_activity(
    email: str,
    first_name: str,
    last_name: str,
    project: str,
    presence: str,
) -> None:
    created_at = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO activity_research (
                email, first_name, last_name, project, presence, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email, first_name, last_name, project, presence, created_at),
        )
        connection.commit()


def _ensure_database() -> None:
    with get_connection() as connection:
        db.init_db(connection)
        db.ensure_users_credentials_column(connection)
        db.ensure_activity_research_name_columns(connection)


def _build_qr_code_data_uri(url: str) -> str | None:
    if importlib.util.find_spec("qrcode") is None:
        return None
    qrcode = importlib.import_module("qrcode")
    qr_image = qrcode.make(url)
    buffer = io.BytesIO()
    qr_image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _get_base_url(request_url: str) -> str:
    base_url = os.environ.get("SITE_COORDINATION_BASE_URL")
    if base_url:
        return base_url
    return _resolve_base_url(request_url)


def _resolve_base_url(request_url: str) -> str:
    if "127.0.0.1" in request_url or "localhost" in request_url:
        resolved = _local_network_url(request_url)
        if resolved:
            return resolved
    return request_url


def _local_network_url(request_url: str) -> str | None:
    try:
        host = request_url.split("//", 1)[1].split("/", 1)[0]
        port = host.split(":", 1)[1] if ":" in host else "5000"
    except IndexError:
        port = "5000"
    ip = _get_lan_ip()
    if not ip:
        return None
    return f"http://{ip}:{port}/"


def _get_lan_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
