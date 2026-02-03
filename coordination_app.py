"""Module shim for running the coordination web app."""

from site_coordination.coordination_app import create_app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
