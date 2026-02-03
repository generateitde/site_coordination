"""Simple web UI for site coordination check-in/out."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

from flask import Flask, flash, redirect, render_template, request, session, url_for

from site_coordination.db_tools import get_connection


def create_app() -> Flask:
    """Create the Flask application."""

    base_dir = Path(__file__).resolve().parent
    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates_checkin"),
        static_folder=str(base_dir / "static"),
    )
    app.secret_key = os.environ.get("SITE_COORDINATION_SECRET", "dev-secret")

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

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
                return redirect(url_for("checkin"))
        return render_template("login.html")

    @app.route("/checkin", methods=["GET", "POST"])
    def checkin() -> str:
        if "user_email" not in session:
            return redirect(url_for("login"))
        email = session["user_email"]
        project = session.get("user_project", "")
        if request.method == "POST":
            presence = request.form.get("presence")
            if presence in {"check-in", "check-out"}:
                _insert_activity(email, project, presence)
                flash("Eintrag gespeichert.", "success")
            else:
                flash("Bitte eine gültige Auswahl treffen.", "error")
        return render_template("checkin.html", email=email, project=project)

    @app.get("/logout")
    def logout() -> str:
        session.clear()
        return redirect(url_for("index"))

    return app


def _fetch_user(email: str) -> Optional[Tuple[str, str]]:
    if not email:
        return None
    with get_connection() as connection:
        row = connection.execute(
            "SELECT password, project FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    if row is None:
        return None
    return row["password"], row["project"]


def _insert_activity(email: str, project: str, presence: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO activity_research (email, project, presence) VALUES (?, ?, ?)",
            (email, project, presence),
        )
        connection.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
