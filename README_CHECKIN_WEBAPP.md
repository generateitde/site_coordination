# CheckIn Webapp

## Voraussetzungen

- Python 3.11+
- Abhängigkeiten installiert: `pip install -r requirements.txt`
- SQLite-Datenbank vorhanden (Standard: `site_coordination.sqlite`)

## Starten der Webapp

1. (Optional) Datenbank initialisieren:
   ```bash
   python -m site_coordination.cli init-db
   ```
2. (Optional) `SITE_COORDINATION_DB` setzen, falls die Datenbank nicht im Projekt-Root liegt:
   ```bash
   export SITE_COORDINATION_DB=/pfad/zur/site_coordination.sqlite
   ```
3. Webapp starten:
   ```bash
   python -m site_coordination.webapp
   ```
4. Im Browser öffnen:
   ```
   http://localhost:5000
   ```

## Ablauf in der Webapp

1. **Seite 1 (Auswahl):** Researcher oder Service Provider auswählen und **Senden**.
2. **Seite 2 (Login, nur Researcher):** E-Mail + Passwort eingeben. **Login** prüft die Daten gegen die `users`-Tabelle in `site_coordination.sqlite`.
3. **Seite 3 (Check-in/Check-out):** Auswahl im Dropdown und **Senden** speichert den Eintrag in `activity_research`.

## Hinweise

- Fehlgeschlagene Logins zeigen eine Fehlermeldung an.
- Für den Produktivbetrieb sollte `SITE_COORDINATION_SECRET` gesetzt werden.
