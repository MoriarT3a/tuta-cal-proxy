# Kalender-Proxy

Ein Proxy-Server für ICS-Kalender mit erweiterter Kompatibilität für verschiedene Kalender-Clients.

## Installation & Start

### Option 1: Mit Docker Compose (empfohlen)

1. Repository klonen:
   ```bash
   git clone https://github.com/yourusername/calendar-proxy.git
   cd calendar-proxy
   ```

2. `.env` Datei erstellen:
   ```bash
   cp .env.example .env
   ```

3. Konfiguration in `.env` anpassen:
   ```
   SOURCE_CALENDAR_URL=https://example.com/calendar.ics
   LOG_LEVEL=INFO
   TZ=Europe/Berlin
   PORT=8098
   ```

4. Mit Docker Compose starten:
   ```bash
   docker-compose up -d
   ```

### Option 2: Manuell

1. Repository klonen:
   ```bash
   git clone https://github.com/yourusername/calendar-proxy.git
   cd calendar-proxy
   ```

2. Python-Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Umgebungsvariablen setzen:
   ```bash
   export SOURCE_CALENDAR_URL=https://example.com/calendar.ics
   export LOG_LEVEL=INFO
   export TZ=Europe/Berlin
   export PORT=8098
   ```

4. Server starten:
   ```bash
   python app.py
   ```

## Nutzung

### 1. Kalender abrufen

Standardzugriff (falls SOURCE_CALENDAR_URL konfiguriert):
```
http://localhost:8098/
```

Mit expliziter Quell-URL:
```
http://localhost:8098/?source=https://example.com/calendar.ics
```

Mit angepasstem Zeitraum (62 Tage in die Vergangenheit, 365 Tage in die Zukunft):
```
http://localhost:8098/?days_before=62&days_after=365
```

### 2. Debug-Informationen anzeigen

Debug-Informationen für einen Kalender anzeigen:
```
http://localhost:8098/debug
```

Mit expliziter Quell-URL:
```
http://localhost:8098/debug?source=https://example.com/calendar.ics
```

### 3. Health-Check

Für Docker-Healthchecks und Monitoring:
```
http://localhost:8098/health
```

## Konfiguration

### Umgebungsvariablen

Die folgenden Umgebungsvariablen können konfiguriert werden:

| Variable | Beschreibung | Standardwert |
|----------|--------------|--------------|
| `SOURCE_CALENDAR_URL` | Die URL des Quell-Kalenders | - |
| `TZ` | Die Zeitzone | Europe/Berlin |
| `LOG_LEVEL` | Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | INFO |
| `PORT` | Der Port, auf dem der Server läuft | 8098 |

### URL-Parameter

Die folgenden URL-Parameter können verwendet werden:

| Parameter | Beschreibung | Standardwert |
|-----------|--------------|--------------|
| `source` | Die URL des Quell-Kalenders | - |
| `days_before` | Anzahl der Tage in die Vergangenheit | 30 |
| `days_after` | Anzahl der Tage in die Zukunft | 365 |
| `debug` | Debug-Modus aktivieren (true/false) | false |

## Problembehandlung

### Health-Check

Überprüfen Sie, ob der Server läuft:
```bash
curl http://localhost:8098/health
```

### Debug-Modus

Setzen Sie `LOG_LEVEL=DEBUG` in der `.env` Datei oder starten Sie den Server mit:
```bash
export LOG_LEVEL=DEBUG
python app.py
```

### Debug-Tool

Verwenden Sie das mitgelieferte debug_calendar.py-Tool:
```bash
python debug_calendar.py --url https://example.com/calendar.ics --proxy-url http://localhost:8098
```

### Docker-Logs

Prüfen Sie die Docker-Logs für Fehlermeldungen:
```bash
docker-compose logs -f
```

## Weitere Informationen

- [Technische Dokumentation](TECHNICAL.md) - Detaillierte technische Beschreibung der Funktionalität
- [Änderungsprotokoll](CHANGELOG.md) - Historie aller Änderungen und Updates

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.