# Technische Dokumentation: Kalender-Proxy v1.1.0

## Systemarchitektur

Der Kalender-Proxy ist als Flask-Anwendung implementiert, die ICS-Kalenderdaten verarbeitet und transformiert. Die Anwendung besteht aus mehreren Kernkomponenten:

### Hauptkomponenten

1. **Flask-Server (app.py)**
   - Initialisiert die Anwendung
   - Konfiguriert Logging
   - Registriert Routen

2. **Kalender-Routen (calendar_routes.py)**
   - `/` und `/calendar`: Hauptendpunkte zum Bereitstellen des verarbeiteten Kalenders
   - `/debug`: Endpunkt zur Analysierung und Anzeige der Kalenderstruktur
   - `/health`: Health-Check-Endpunkt für Docker

3. **Kalender-Verarbeitung (ical_processor.py)**
   - Zentrale Importdatei, die alle nötigen Funktionalitäten aus verschiedenen Modulen zusammenführt

4. **Basisfunktionen (base.py)**
   - `sanitize_calendar`: Bereinigt einen Kalender
   - `create_instance_from_recurring`: Erstellt Instanzen wiederkehrender Termine
   - `extract_excluded_dates`: Extrahiert ausgeschlossene Termine
   - `get_date_string`: Erzeugt konsistente Datumsstrings

5. **Expansion von wiederkehrenden Terminen (expand.py)**
   - `expand_recurring_event`: Hauptfunktion zur Expansion wiederkehrender Termine
   - Intelligente Dual-Strategie mit automatischer und manueller Expansion

6. **Frequenzspezifische Expansionsfunktionen (frequency.py)**
   - `expand_daily`: Expandiert tägliche wiederkehrende Termine
   - `expand_weekly`: Expandiert wöchentliche wiederkehrende Termine
   - `expand_monthly`: Expandiert monatliche wiederkehrende Termine
   - `manually_expand_recurring_event`: Fallback-Methode für komplexe Fälle

7. **Spezialfunktionen für bestimmte Wiederholungstypen**
   - `monthly.py`: Spezialfunktionen für monatliche Wiederholungen
   - `yearly.py`: Spezialfunktionen für jährliche Wiederholungen

8. **Debug-Tools (debug_calendar.py)**
   - Standalone-Skript zur Analyse und Diagnostik von Kalender-Dateien

## Datenfluss

1. Der Client fordert einen Kalender an (`/calendar` oder `/`)
2. Der Server lädt die ICS-Datei von der Quell-URL
3. Die Kalender-Daten werden geparst und analysiert
4. Einzeltermine werden direkt übernommen (mit angepasster UID)
5. Wiederkehrende Termine werden expandiert:
   a. Versuch der automatischen Expansion mit dateutil.rrule
   b. Bei Problemen: Fallback auf manuelle Expansion
   c. Spezielle Behandlung für kurze Zeiträume und UNTIL-Datum
6. Ausnahmen und ausgeschlossene Termine werden berücksichtigt
7. Alle expandierten Instanzen werden dem neuen Kalender hinzugefügt
8. Der transformierte Kalender wird an den Client zurückgesendet

## Kernalgorithmen

### Expansion wiederkehrender Termine

Die `expand_recurring_event`-Funktion verwendet einen mehrstufigen Ansatz:

1. **Vorbereitung**
   - Extraktion des UNTIL-Datums
   - Bestimmung des effektiven Zeitraums
   - Früherkennung von kurzen Terminserien

2. **Automatische Expansion**
   - Bereinigung und Validierung der RRULE
   - Konvertierung in dateutil.rrule-Format
   - Berechnung der Termininstanzen

3. **Validierung**
   - Bei wenigen Instanzen: Abgleich mit manueller Expansion
   - Bei Diskrepanzen: Bevorzugung der manuellen Ergebnisse

4. **Instanzerstellung**
   - Filterung ausgeschlossener Daten
   - Berücksichtigung von Ausnahmen
   - Generierung eindeutiger UIDs

### Manuelle Expansion

Der manuelle Expansionsalgorithmus in `manually_expand_recurring_event`:

1. **Typspezifische Expansion**
   - Für jede Frequenz (täglich, wöchentlich, monatlich, jährlich) gibt es optimierte Algorithmen
   - Besondere Behandlung für kurze Zeiträume mit spezifischen Wochentagen

2. **Wochentagsberechnung (für wöchentliche Termine)**
   - Extraktion der BYDAY-Werte mit regulären Ausdrücken
   - Berechnung der Wochenintervalle
   - Tag-für-Tag-Iteration mit präzisen Bedingungen

3. **Datumsberechnung**
   - Korrekte Beibehaltung von Zeitzonen
   - Berücksichtigung von ganztägigen und Terminen mit Uhrzeit
   - Präzise Interval-Berechnung

## Konfigurationsoptionen

Der Kalender-Proxy kann über verschiedene Methoden konfiguriert werden:

1. **Umgebungsvariablen**
   - `SOURCE_CALENDAR_URL`: Quell-URL des Kalenders
   - `LOG_LEVEL`: Debug-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - `PORT`: Server-Port (Standard: 8098)
   - `TZ`: Zeitzone (Standard: Europe/Berlin)

2. **URL-Parameter**
   - `source`: Explizite Angabe der Kalender-URL
   - `days_before`: Anzahl der Tage vor dem aktuellen Datum (Standard: 30)
   - `days_after`: Anzahl der Tage nach dem aktuellen Datum (Standard: 365)
   - `debug`: Debug-Modus aktivieren (true/false)

3. **Docker-Umgebung**
   - Über docker-compose.yaml konfigurierbar
   - Volume-Mapping für Logs
   - Health-Check und Ressourcenlimits

## Fehlerbehandlung

Der Kalender-Proxy implementiert eine robuste Fehlerbehandlung:

1. **Graceful Degradation**
   - Bei Fehlern in der automatischen Expansion: Fallback auf manuelle Methoden
   - Bei Parsing-Problemen: Informative Fehlermeldungen

2. **Ausführliches Logging**
   - Detailliertes Logging aller Verarbeitungsschritte im DEBUG-Modus
   - Warnungen bei problematischen RRULE-Eigenschaften

3. **Debug-Endpunkt**
   - `/debug` liefert detaillierte Informationen zur Kalenderstruktur
   - Analyse von Komponenten, Events und Zeitzonen

## Performance-Überlegungen

1. **Effizienz**
   - Intelligente Filterung von Terminen außerhalb des Zeitraums
   - Optimierte Expansion wiederkehrender Termine

2. **Skalierbarkeit**
   - Containerisierbare Anwendung mit Docker
   - Konfigurierbare Ressourcenlimits

3. **Caching**
   - Keine direkte Implementierung, kann jedoch über einen Reverse-Proxy erfolgen

## Bekannte Einschränkungen

1. **Komplexe Wiederholungsregeln**
   - Sehr komplexe RRULE-Eigenschaften könnten in seltenen Fällen nicht korrekt expandiert werden
   - Bei Problemen empfehlen sich Tests mit dem Debug-Tool

2. **Kalendergröße**
   - Sehr große Kalender mit vielen wiederkehrenden Terminen können zu erhöhtem Speicherverbrauch führen
   - Limitierung des Zeitraums über `days_before` und `days_after` empfohlen

## Zukunftspläne

Mögliche zukünftige Erweiterungen könnten sein:

1. **Caching-Mechanismus** für häufig abgerufene Kalender
2. **Verbesserte Validierung** für noch komplexere RRULE-Eigenschaften
3. **API-Erweiterungen** für gezieltere Kalenderoperationen
4. **Performance-Optimierungen** für sehr große Kalender