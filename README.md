# Änderungen in Version 1.1.0

## Übersicht

Version 1.1.0 des Kalender-Proxys enthält mehrere bedeutende Verbesserungen, die insbesondere die Handhabung von wiederkehrenden Terminen verbessern. Diese Aktualisierungen erhöhen die Kompatibilität mit verschiedenen Kalender-Clients und beheben Fehler bei der Expansion von wiederkehrenden Ereignissen.

## Hauptänderungen

### 1. Verbesserte Behandlung von UNTIL-Daten in wiederkehrenden Terminen

* Korrekte Interpretation und Anwendung des UNTIL-Datums bei der Expansion von wiederkehrenden Terminen
* Terminserie endet jetzt zuverlässig am angegebenen UNTIL-Datum anstatt inkorrekt weiter zu laufen
* Sorgfältige Datumsberechnung unter Berücksichtigung verschiedener Zeitzonenformate

### 2. Spezielle Verarbeitung für Termine mit kurzen Zeiträumen

* Intelligente Erkennung und Spezialbehandlung für Termine, die nur über einen kurzen Zeitraum wiederholt werden
* Korrekte Expansion von Terminen, die innerhalb weniger Tage mehrfach wiederholt werden
* Tag-genaue Iteration für Termine mit spezifischen Wochentagen und kurzen Zeiträumen

### 3. Robustheit gegen fehlerhafte RRULE-Eigenschaften

* Verbesserte Validierung und Bereinigung von RRULE-Eigenschaften
* Fallback auf manuelle Expansion bei Problemen mit der automatischen dateutil.rrule-Methode
* Bessere Fehlerbehandlung und informative Logging-Nachrichten

### 4. Optimierte Verarbeitungslogik

* Duale Expansionsstrategie mit automatischer und manueller Methode für maximale Kompatibilität
* Zusätzliche Validierung für Termine mit geringer Anzahl an Wiederholungen
* Verbesserte Performance durch intelligentere Algorithmen

## Technische Details

### Behandlung von wiederkehrenden Terminen (in expand.py)

Die neue `expand_recurring_event`-Funktion enthält jetzt mehrere Optimierungen:

* Frühzeitige Erkennung von kurzen Zeiträumen
* Spezielle Behandlung für Termine mit UNTIL-Datum
* Validierung der generierten Instanzen für höhere Zuverlässigkeit

### Spezialverarbeitung für wöchentliche Termine (in frequency.py)

Die `expand_weekly`-Funktion wurde überarbeitet, um insbesondere Termine mit UNTIL-Datum korrekt zu behandeln:

* Verbesserte Berechnung der Wochenintervalle
* Korrekte Berücksichtigung des UNTIL-Datums bei der Termingeneration
* Robustere Verarbeitung verschiedener BYDAY-Formate

### Manuelle Expansion (in events.py)

Die manuelle Expansion wurde komplett überarbeitet:

* Präzisere Tag-für-Tag-Iteration für kurze Zeiträume
* Verbesserte Wochentagsberechnung
* Korrekte Behandlung von Ausnahmen und ausgeschlossenen Daten (EXDATE)

## Behobene Probleme

* **UNTIL-Datum nicht beachtet**: Wiederkehrende Termine mit definiertem Enddatum (UNTIL) laufen nicht mehr über dieses Datum hinaus
* **Fehlerhafte wöchentliche Wiederholung**: Korrekte Berechnung für Termine, die nur an bestimmten Wochentagen innerhalb eines kurzen Zeitraums stattfinden
* **Importfehler in Modulen**: Korrekte Importe für alle benötigten Module, einschließlich 're' für reguläre Ausdrücke
* **Fehlendes 'get_date_string'**: Implementierung der fehlenden Funktion zur Datumsformatierung
* **Fehlerhafte relative Importe**: Korrektur der Importpfade in calendar_routes.py

## Kompatibilität

Diese Aktualisierung verbessert die Kompatibilität mit folgenden Kalendersystemen:
* Tuta-Kalender
* Google Kalender
* Apple Kalender
* Outlook 365
* Thunderbird Lightning
* NextCloud Kalender

## Empfohlene Aktionen für Benutzer

* Aktualisieren Sie auf Version 1.1.0, um von den verbesserten Wiederholungsregeln zu profitieren
* Wenn Sie eigene Anpassungen vorgenommen haben, integrieren Sie diese sorgfältig in die aktualisierte Codebasis
* Testen Sie die neue Version mit Ihren speziellen Kalenderszenarien, insbesondere bei komplexen wiederkehrenden Terminen
* Prüfen Sie bei Problemen den Debug-Endpunkt und die Logs für detaillierte Informationen
