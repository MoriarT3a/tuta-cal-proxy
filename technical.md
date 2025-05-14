# Kalender-Proxy: Technische Dokumentation

## Funktionsübersicht

Der Kalender-Proxy ist ein spezialisierter Server, der ICS-Kalenderdaten verarbeitet und transformiert, um die Kompatibilität mit verschiedenen Kalender-Clients zu verbessern. Die Hauptfunktionalität besteht in der Vorexpansion wiederkehrender Ereignisse in einzelne Ereignisse, was insbesondere für Clients wie den Tuta-Kalender die Darstellung verbessert.

## Hauptfunktionen

### 1. Vorexpansion wiederkehrender Ereignisse

- **Vollständige Unterstützung aller RRULE-Typen**:
  - Tägliche Wiederholungen (FREQ=DAILY)
  - Wöchentliche Wiederholungen (FREQ=WEEKLY)
  - Monatliche Wiederholungen (FREQ=MONTHLY)
  - Jährliche Wiederholungen (FREQ=YEARLY)

- **UNTIL-Datum-Unterstützung**:
  - Präzise Einhaltung des Enddatums für wiederkehrende Termine
  - Korrekte Verarbeitung verschiedener Zeitzonenformate

- **BYDAY-Eigenschaften für wöchentliche Termine**:
  - Korrekte Handling von spezifischen Wochentagen (MO, TU, WE, TH, FR, SA, SU)
  - Unterstützung für Positionsangaben (z.B. 1MO, -1FR)

- **Spezielle Behandlung kurzer Zeiträume**:
  - Optimierte Verarbeitung für Termine mit nur wenigen Wiederholungen
  - Tag-genaue Iteration für höchste Präzision

### 2. Kalender-Transformation und -Bereinigung

- **UID-Management**:
  - Generierung konsistenter und eindeutiger Event-IDs
  - Verhinderung von Duplikaten und Konflikten

- **Zeitzonen-Verarbeitung**:
  - Beibehaltung der Zeitzoneninfos bei der Expansion
  - Korrekte Berücksichtigung von ganztägigen und Terminen mit Uhrzeit

- **Metadaten-Erhaltung**:
  - Beibehaltung wichtiger Kalender-Eigenschaften (PRODID, VERSION, METHOD)
  - Erhaltung von VTIMEZONE-Komponenten

### 3. Robuste Fehlerbehandlung

- **Dual-Strategie für Expansion**:
  - Primär: Automatische Expansion mit dateutil.rrule
  - Fallback: Manuelle Expansion für problematische Fälle

- **Ausnahmeverarbeitung**:
  - Korrekte Behandlung von EXDATE (ausgeschlossenen Terminen)
  - Unterstützung für Ausnahmen (recurrence-id)

- **Validierung und Bereinigung**:
  - Prüfung und Korrektur von RRULE-Eigenschaften
  - Zusätzliche Validierung für Termine mit wenigen Wiederholungen

## Systemarchitektur

### Komponenten

1. **Flask-Webserver (app.py)**
   - Initialisiert die Anwendung und konfiguriert Logging
   - Registriert die Kalender-Routen

2. **Kalender-Routen (calendar_routes.py)**
   - Definiert die API-Endpunkte
   - Verarbeitet eingehende Anfragen

3. **Kalender-Prozessor (ical_processor.py)**
   - Zentrale Importdatei für die Kalenderverarbeitung
   - Vereint alle Funktionalitäten

4. **Basisfunktionen (base.py)**
   - Grundlegende Hilfsfunktionen für die Kalenderverarbeitung
   - Kalendererstellung und -bereinigung

5. **Expansion-Module**
   - **expand.py**: Hauptfunktion zur Expansion wiederkehrender Termine
   - **frequency.py**: Frequenzspezifische Expansionsalgorithmen
   - **monthly.py**: Spezialisierte Funktionen für monatliche Termine
   - **yearly.py**: Spezialisierte Funktionen für jährliche Termine

6. **Debug-Tool (debug_calendar.py)**
   - Standalone-Skript zur Analyse und Diagnose von Kalendern

### Datenfluss

1. Der Client fordert einen Kalender an (`/calendar` oder `/`)
2. Der Server lädt die ICS-Datei von der konfigurierten oder angegebenen Quell-URL
3. Die Kalender-Daten werden geparst und in ihre Komponenten zerlegt
4. Einzeltermine werden direkt übernommen (mit angepasster UID)
5. Wiederkehrende Termine werden expandiert:
   - Automatische Expansion wird versucht
   - Bei Problemen erfolgt Fallback auf manuelle Expansion
   - Instanzen außerhalb des Zeitraums werden ignoriert
6. Alle expandierten Instanzen werden dem neuen Kalender hinzugefügt
7. Der transformierte Kalender wird als ICS-Datei an den Client zurückgesendet

## Algorithmen im Detail

### Expansion wiederkehrender Termine

Die `expand_recurring_event`-Funktion in `expand.py` implementiert folgende Logik:

1. **Analyse des wiederkehrenden Termins**:
   - Extraktion von DTSTART, RRULE und UNTIL-Datum
   - Bestimmung des effektiven Zeitraums basierend auf UNTIL und angeforderten Daten

2. **Früherkennung von Spezialfällen**:
   - Identifikation von kurzen Zeiträumen (≤7 Tage)
   - Spezialbehandlung für Termine mit definiertem UNTIL-Datum

3. **Automatische Expansion**:
   - Bereinigung von RRULE-Eigenschaften
   - Konvertierung in dateutil.rrule-Format
   - Berechnung der Termininstanzen

4. **Zusätzliche Validierung**:
   - Bei wenigen Instanzen (1-3): Vergleich mit manueller Expansion
   - Bei Diskrepanzen: Verwendung der manuellen Ergebnisse

5. **Nachbearbeitung**:
   - Filterung ausgeschlossener Daten (EXDATE)
   - Berücksichtigung von Ausnahmen (recurrence-id)
   - Erstellung eindeutiger UIDs für alle Instanzen

### Spezialbehandlung für kurze Zeiträume

Bei wöchentlichen Terminen mit kurzen Zeiträumen (≤7 Tage):

1. **Extraktion der Wochentage**:
   - BYDAY-Werte werden mit regulären Ausdrücken gefiltert
   - Konvertierung in numerische Wochentage (0-6)

2. **Tag-für-Tag-Iteration**:
   - Durchlaufen aller Tage im Zeitraum
   - Prüfung auf passende Wochentage

3. **Präzise Termingeneration**:
   - Erstellung von Instanzen nur für passende Tage
   - Exakte Beibehaltung der Originalzeit

## Kompatibilität

Der Kalender-Proxy ist so konzipiert, dass er mit einer Vielzahl von Kalendersystemen kompatibel ist:

- **Tuta-Kalender**: Primäres Ziel der Optimierungen
- **Google Kalender**: Vollständig unterstützt
- **Apple Kalender**: Vollständig unterstützt
- **Outlook 365**: Vollständig unterstützt
- **Thunderbird Lightning**: Vollständig unterstützt
- **NextCloud Kalender**: Vollständig unterstützt

## Bekannte Einschränkungen

- Sehr komplexe Wiederholungsregeln mit mehreren BYXXX-Eigenschaften könnten in seltenen Fällen nicht korrekt expandiert werden
- Sehr große Kalender mit vielen wiederkehrenden Terminen können zu erhöhtem Speicherverbrauch führen
- Die Anwendung implementiert kein Caching, jede Anfrage führt zu einer erneuten Verarbeitung

## Performance-Optimierungen

- Intelligente Filterung von Terminen außerhalb des angeforderten Zeitraums
- Optimierte Expansion wiederkehrender Termine basierend auf Termintyp
- Frühe Erkennung und spezielle Verarbeitung von Sonderfällen