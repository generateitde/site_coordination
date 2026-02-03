"""Run the coordination dashboard locally."""

from site_coordination.coordination_app import create_app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
