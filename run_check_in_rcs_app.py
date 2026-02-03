"""Run the CheckIn RCS Flask app from the repo root."""

from site_coordination.check_in_rcs_app import create_app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True)
