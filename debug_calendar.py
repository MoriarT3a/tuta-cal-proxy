#!/usr/bin/env python3
"""
Debug-Tool für Calendar-Proxy.
Dieses Skript lädt einen Kalender, analysiert ihn und testet verschiedene Problembereiche.
"""

import sys
import os
import argparse
import requests
import json
import logging
from icalendar import Calendar, Event

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('ical-debugger')

def check_ical(calendar_url):
    """Überprüft eine .ics-Datei auf Standardkonformität"""
    logger.info(f"Überprüfe Kalender von URL: {calendar_url}")
    
    try:
        # Kalender herunterladen
        response = requests.get(calendar_url)
        response.raise_for_status()
        
        cal_content = response.content
        logger.info(f"Kalendergröße: {len(cal_content)} Bytes")
        
        # Versuche, den Kalender zu parsen
        try:
            cal = Calendar.from_ical(cal_content)
            logger.info("✓ Kalender konnte erfolgreich geparst werden")
        except Exception as e:
            logger.error(f"✗ Fehler beim Parsen des Kalenders: {e}")
            return False
        
        # Prüfe Grundkomponenten
        component_counts = {}
        for component in cal.walk():
            comp_name = component.name
            if comp_name not in component_counts:
                component_counts[comp_name] = 0
            component_counts[comp_name] += 1
        
        logger.info(f"Kalenderkomponenten: {component_counts}")
        
        # Prüfe auf VCALENDAR
        if 'VCALENDAR' not in component_counts:
            logger.error("✗ Keine VCALENDAR-Komponente gefunden")
            return False
        
        # Prüfe auf Events
        if 'VEVENT' not in component_counts:
            logger.error("✗ Keine VEVENT-Komponenten gefunden")
            return False
        
        # Prüfe wiederkehrende Ereignisse
        recurring_events = 0
        normal_events = 0
        exception_events = 0
        
        for event in cal.walk('VEVENT'):
            if event.get('recurrence-id'):
                exception_events += 1
            elif event.get('rrule'):
                recurring_events += 1
            else:
                normal_events += 1
        
        logger.info(f"Normale Ereignisse: {normal_events}")
        logger.info(f"Wiederkehrende Ereignisse: {recurring_events}")
        logger.info(f"Ausnahme-Ereignisse: {exception_events}")
        
        # Prüfe auf häufige Probleme
        issues = []
        
        # UIDs prüfen
        unique_uids = set()
        duplicate_uids = set()
        
        for event in cal.walk('VEVENT'):
            uid = str(event.get('uid', ''))
            if not uid:
                issues.append("Event ohne UID gefunden")
            elif uid in unique_uids:
                duplicate_uids.add(uid)
            else:
                unique_uids.add(uid)
        
        if duplicate_uids:
            issues.append(f"Doppelte UIDs gefunden: {len(duplicate_uids)} Stück")
        
        # Zeitzonenprobleme
        tz_issues = False
        for event in cal.walk('VEVENT'):
            dtstart = event.get('dtstart')
            if dtstart and hasattr(dtstart.dt, 'tzinfo') and dtstart.dt.tzinfo is None:
                tz_issues = True
                break
        
        if tz_issues:
            issues.append("Einige Ereignisse haben keine Zeitzone definiert")
        
        # DTSTAMP fehlt
        dtstamp_issues = False
        for event in cal.walk('VEVENT'):
            if 'dtstamp' not in event:
                dtstamp_issues = True
                break
        
        if dtstamp_issues:
            issues.append("Einige Ereignisse haben kein DTSTAMP")
        
        # Berichte die gefundenen Probleme
        if issues:
            logger.warning("⚠ Folgende Probleme wurden erkannt:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("✓ Keine offensichtlichen Probleme gefunden")
        
        return True
    
    except requests.RequestException as e:
        logger.error(f"✗ Fehler beim Herunterladen des Kalenders: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unerwarteter Fehler: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Debug-Tool für Calendar-Proxy")
    parser.add_argument("--url", help="Die URL des zu testenden Kalenders")
    parser.add_argument("--proxy-url", help="Die URL des Calendar-Proxy (z.B. http://localhost:8098)")
    
    args = parser.parse_args()
    
    if not args.url and not args.proxy_url:
        parser.print_help()
        sys.exit(1)
    
    # Prüfe Quell-Kalender, wenn URL angegeben
    if args.url:
        logger.info("== Analyse des Quell-Kalenders ==")
        check_ical(args.url)
    
    # Prüfe Proxy-Kalender, wenn URL angegeben
    if args.proxy_url:
        proxy_url = args.proxy_url
        if not proxy_url.endswith('/'):
            proxy_url += '/'
        
        logger.info("== Analyse des Proxy-Kalenders ==")
        
        # Proxy-Parameter hinzufügen, falls Quell-URL angegeben wurde
        if args.url:
            if '?' in proxy_url:
                proxy_url += f"&source={args.url}"
            else:
                proxy_url += f"?source={args.url}"
        
        check_ical(proxy_url)
        
        # Debug-Endpunkt abrufen für weitere Informationen
        try:
            debug_url = f"{args.proxy_url.rstrip('/')}/debug"
            if args.url:
                if '?' in debug_url:
                    debug_url += f"&source={args.url}"
                else:
                    debug_url += f"?source={args.url}"
            
            logger.info(f"Rufe Debug-Endpunkt ab: {debug_url}")
            debug_response = requests.get(debug_url)
            
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                logger.info(f"Debug-Informationen:")
                logger.info(json.dumps(debug_data, indent=2))
            else:
                logger.error(f"Fehler beim Abrufen des Debug-Endpunkts: {debug_response.status_code}")
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Debug-Endpunkts: {e}")

if __name__ == "__main__":
    main()
