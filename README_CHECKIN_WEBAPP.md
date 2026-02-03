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
3. Start the webapp:
   ```bash
   python -m site_coordination.webapp
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
