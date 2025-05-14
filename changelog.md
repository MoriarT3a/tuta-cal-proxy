# Änderungsprotokoll

## Version 1.1.0 (2025-05-14)

### Wesentliche Verbesserungen

- **Verbesserte Behandlung von wiederkehrenden Terminen mit UNTIL-Datum**
  - Termine enden jetzt korrekt am angegebenen UNTIL-Datum
  - Korrekte Verarbeitung von Zeitzonenformaten im UNTIL-Datum
  - Spezifische Validierung der generierten Instanzen

- **Neue Behandlung von kurzen wiederkehrenden Terminserien**
  - Optimierte Verarbeitung für Serien mit wenigen Wiederholungen
  - Spezielle Tag-für-Tag-Iteration für höchste Präzision
  - Verbesserte Algorithmen für wöchentliche Wiederholungen an spezifischen Wochentagen

- **Verbesserte Robustheit gegen fehlerhafte Kalenderdaten**
  - Optimierte Fehlerbehandlung bei problematischen RRULE-Eigenschaften
  - Fallback-Mechanismen für nicht-standardkonforme Kalender
  - Bessere Warnungen und Debug-Informationen

- **Dual-Strategie für Terminexpansion**
  - Primär: Automatische Expansion mit dateutil.rrule
  - Sekundär: Robuste manuelle Expansion für komplexe Fälle
  - Validierung und Vergleich beider Methoden für kritische Termine

### Behobene Probleme

- **Fehler bei der Verarbeitung von UNTIL-Daten**
  - Termine mit definiertem Enddatum (UNTIL) laufen nicht mehr über dieses Datum hinaus
  - Korrekte Berechnung des effektiven Enddatums basierend auf UNTIL und angeforderten Daten

- **Fehlerhafte Expansion wöchentlicher Termine**
  - Korrektur der Berechnung für Termine, die nur an bestimmten Wochentagen stattfinden
  - Präzise Berücksichtigung des Startdatums und Wochenintervalls

- **Import-Probleme und fehlende Funktionen**
  - Korrektur fehlerhafter relativer Importe in calendar_routes.py
  - Implementierung der fehlenden `get_date_string`-Funktion
  - Hinzufügung des fehlenden `re`-Modul-Imports in `frequency.py`

- **Technische Schulden**
  - Verbesserung der Code-Qualität und -Struktur
  - Entfernung von hardcodierten UIDs und Terminnamen

### Technische Änderungen

- **File: base.py**
  - Neue Funktion `get_date_string` zur konsistenten Datumsformatierung
  - Verbesserte Validierung in `sanitize_rrule`

- **File: expand.py**
  - Überarbeitete `expand_recurring_event`-Funktion mit Spezialerkennung kurzer Zeiträume
  - Zusätzliche Validierungsschritte für kritische Termine

- **File: frequency.py**
  - Korrektur des fehlenden `re`-Modul-Imports
  - Verbesserte `expand_weekly`-Funktion mit korrekter Wochentagsberechnung
  - Optimierte manuelle Expansion für alle Frequenztypen

- **File: calendar_routes.py**
  - Korrektur von relativen Import-Pfaden
  - Robustere Fehlerbehandlung

- **File: ical_processor.py**
  - Aktualisierte Import-Liste mit `get_date_string`
  - Verbesserte Modulstruktur

## Version 1.0.0 (2025-03-01)

- Erstveröffentlichung
- Grundlegende Funktionalität zur Expansion wiederkehrender Termine
- Unterstützung für tägliche, wöchentliche, monatliche und jährliche Wiederholungen
- Basisimplementierung der Kalenderbereinigung und -transformation