# CheckIn Webapp

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`
- SQLite database available (default: `database/site_coordination.sqlite`)

## Start the webapp

1. (Optional) Initialize the database:
   ```bash
   python -m site_coordination.cli init-db
   ```
2. (Optional) Set `SITE_COORDINATION_DB` if the database is not in `database/`:
   ```bash
   export SITE_COORDINATION_DB=/path/to/site_coordination.sqlite
   ```
3. Start the webapp from the repository root:
   ```bash
   python run_check_in_rcs_app.py
   ```
   Alternatively:
   ```bash
   python -m site_coordination.check_in_rcs_app
   ```
4. Open in the browser:
   ```
   http://localhost:5000
   ```

## Flow inside the webapp

1. **Page 1 (Selection):** Choose Researcher or Service Provider and click **Send**.
2. **Page 2 (Login, Researcher only):** Enter email + password. **Login** validates against the `users`
   table in `site_coordination.sqlite`.
3. **Page 3 (Check-in/Check-out):** Choose the dropdown value and click **Send** to store the entry in
   `activity_research`.

## Notes

- Failed logins show an error message.
- For production, set `SITE_COORDINATION_SECRET`.
- For a local network demo QR code, set `SITE_COORDINATION_BASE_URL` to your LAN IP
  (for example, `http://192.168.1.50:5001/`) so other devices can scan the code.
  Ensure the app is running with `host=0.0.0.0` (default in `run_check_in_rcs_app.py`)
  and that your firewall allows inbound traffic on the port.
- If you want a purely local QR code (no external service), install `qrcode[pil]` and the server
  will embed a PNG. Otherwise the app falls back to a hosted QR image (requires internet access).
- If `SITE_COORDINATION_BASE_URL` is not set and the app is opened via localhost, the check-in app
  attempts to resolve your LAN IP automatically so the QR code points at a reachable address.

## Troubleshooting

- **BuildError: Could not build url for endpoint 'registrations'**: Ensure you have pulled the
  latest changes so the `/registrations` route exists, or remove any older template link that
  references `url_for('registrations')`.
- **BuildError: Could not build url for endpoint 'bookings'**: Ensure you have pulled the latest
  changes so the `/bookings` route exists, or remove any older template link that references
  `url_for('bookings')`.
