from flask import Blueprint, Response, request, jsonify
import os
import logging
import requests
import datetime
from cal_utils.ical_processor import (
    Calendar, sanitize_calendar, extract_excluded_dates, 
    expand_recurring_event
)

logger = logging.getLogger('ical-proxy')

calendar_routes = Blueprint('calendar', __name__)

@calendar_routes.route('/health')
def health_check():
    """Health-Check-Endpunkt für Docker-Healthcheck"""
    return jsonify({"status": "healthy"}), 200

@calendar_routes.route('/debug')
def debug_calendar():
    """Debug-Endpunkt zum Anzeigen der Original-Kalenderstruktur"""
    # Hier ist die Quell-URL - sie kann explizit als Parameter oder als Umgebungsvariable gesetzt sein
    default_url = os.environ.get('SOURCE_CALENDAR_URL', '')
    calendar_url = request.args.get('source', default_url)
    
    # Prüfen, ob eine URL angegeben wurde
    if not calendar_url:
        return "Keine Kalender-URL angegeben. Bitte setze die SOURCE_CALENDAR_URL Umgebungsvariable oder füge '?source=https://deine-kalender-url.ics' zur Anfrage hinzu.", 400
    
    try:
        # Kalender herunterladen
        response = requests.get(calendar_url)
        response.raise_for_status()
        
        cal_content = response.content
        
        # Original-Kalender parsen
        cal = Calendar.from_ical(cal_content)
        
        # Debuginformationen sammeln
        debug_info = {
            "calendar_size": len(cal_content),
            "components": {},
            "events": [],
            "timezones": []
        }
        
        # Komponenten zählen
        for component in cal.walk():
            comp_name = component.name
            if comp_name not in debug_info["components"]:
                debug_info["components"][comp_name] = 0
            debug_info["components"][comp_name] += 1
        
        # Termine analysieren
        for event in cal.walk('VEVENT'):
            event_info = {
                "uid": str(event.get('uid', '')),
                "summary": str(event.get('summary', '')),
                "has_rrule": 'rrule' in event,
                "has_exdate": 'exdate' in event,
                "has_recurrence_id": 'recurrence-id' in event
            }
            
            if 'rrule' in event:
                event_info["rrule"] = {}
                for key, val in event['rrule'].items():
                    if isinstance(val, list):
                        event_info["rrule"][key] = [str(v) for v in val]
                    else:
                        event_info["rrule"][key] = str(val)
            
            debug_info["events"].append(event_info)
        
        # Zeitzonen analysieren
        for tz in cal.walk('VTIMEZONE'):
            tz_info = {
                "tzid": str(tz.get('tzid', '')),
                "has_daylight": any(c.name == 'DAYLIGHT' for c in tz.subcomponents),
                "has_standard": any(c.name == 'STANDARD' for c in tz.subcomponents)
            }
            debug_info["timezones"].append(tz_info)
        
        return jsonify(debug_info)
    
    except Exception as e:
        logger.exception("Fehler beim Analysieren des Kalenders")
        return f"Fehler beim Analysieren des Kalenders: {str(e)}", 500

@calendar_routes.route('/')
@calendar_routes.route('/calendar')
def serve_simplified_calendar():
    """Hauptendpunkt zum Bereitstellen des vereinfachten Kalenders"""
    # Hier ist die Quell-URL - sie kann explizit als Parameter oder als Umgebungsvariable gesetzt sein
    default_url = os.environ.get('SOURCE_CALENDAR_URL', '')
    calendar_url = request.args.get('source', default_url)
    
    # Protokollieren der verwendeten URL (für Debug-Zwecke)
    logger.info(f"Using calendar URL: {calendar_url}")
    
    # Prüfen, ob eine URL angegeben wurde
    if not calendar_url:
        logger.error("No calendar URL specified")
        return "Keine Kalender-URL angegeben. Bitte setze die SOURCE_CALENDAR_URL Umgebungsvariable oder füge '?source=https://deine-kalender-url.ics' zur Anfrage hinzu.", 400
    
    # Parameter für den Zeitraum
    days_before = int(request.args.get('days_before', 30))
    days_after = int(request.args.get('days_after', 365))
    
    # Debug-Modus?
    debug_mode = request.args.get('debug', 'false').lower() == 'true'
    
    # Zeitraum für die Terminexpansion
    start_date = datetime.datetime.now().date() - datetime.timedelta(days=days_before)
    end_date = datetime.datetime.now().date() + datetime.timedelta(days=days_after)
    
    logger.info(f"Date range: {start_date} to {end_date}")
    
    try:
        # Kalender herunterladen
        logger.info(f"Downloading calendar from {calendar_url}")
        response = requests.get(calendar_url)
        response.raise_for_status()  # Wirft Fehler bei HTTP-Fehlercodes
        
        cal_content = response.content
        logger.info(f"Downloaded calendar, size: {len(cal_content)} bytes")
        
        # Original-Kalender parsen
        cal = Calendar.from_ical(cal_content)
        
        # Neuen Kalender erstellen
        new_cal = sanitize_calendar(cal)
        
        # Termine nach Typ sortieren
        normal_events = []
        recurring_events = {}
        exceptions = {}
        
        for component in cal.walk('VEVENT'):
            uid = str(component.get('uid', ''))
            
            # Nach Typ sortieren
            if component.get('recurrence-id'):
                # Ausnahme für wiederkehrenden Termin
                if uid not in exceptions:
                    exceptions[uid] = []
                exceptions[uid].append(component)
            elif component.get('rrule'):
                # Wiederkehrender Termin
                recurring_events[uid] = component
            else:
                # Normaler Einzeltermin
                normal_events.append(component)
        
        # Normale Termine übernehmen, wenn sie im Zeitraum liegen
        for event in normal_events:
            dtstart = event.get('dtstart').dt
            
            # Prüfen, ob im Zeitraum
            if isinstance(dtstart, datetime.datetime):
                event_date = dtstart.date()
            else:
                event_date = dtstart
            
            if start_date <= event_date <= end_date:
                # UID anpassen, um Konflikte zu vermeiden
                event_uid = str(event.get('uid', ''))
                # Stabile UID generieren
                if isinstance(dtstart, datetime.datetime):
                    date_str = dtstart.date().isoformat()
                else:
                    date_str = dtstart.isoformat()
                
                stable_uid = f"{event_uid}-{date_str}"
                event['uid'] = stable_uid
                
                new_cal.add_component(event)
        
        # Wiederkehrende Termine expandieren
        for uid, event in recurring_events.items():
            # Ausnahmen für diesen wiederkehrenden Termin
            event_exceptions = exceptions.get(uid, [])
            
            # Ausgeschlossene Termine extrahieren
            excluded_dates = extract_excluded_dates(event)
            
            # Zusätzliches Logging für Debugging
            if 'summary' in event:
                summary = str(event.get('summary', ''))
                dtstart = event.get('dtstart').dt
                start_str = dtstart.isoformat() if hasattr(dtstart, 'isoformat') else str(dtstart)
                
                if 'rrule' in event:
                    rrule_info = {}
                    for key, val in event['rrule'].items():
                        if isinstance(val, list):
                            rrule_info[key] = [str(v) for v in val]
                        else:
                            rrule_info[key] = str(val)
                    
                    logger.debug(f"Expandiere wiederkehrenden Termin: '{summary}' mit Start {start_str}, RRULE: {rrule_info}")
                else:
                    logger.debug(f"Expandiere wiederkehrenden Termin: '{summary}' mit Start {start_str}")
            
            # Expandieren
            expanded_instances = expand_recurring_event(
                event, start_date, end_date, event_exceptions, excluded_dates
            )
            
            # Logging der expandierten Termine
            if debug_mode and expanded_instances:
                summary = str(event.get('summary', 'Unbekannt'))
                dates_str = ', '.join([
                    instance.get('dtstart').dt.isoformat() 
                    if hasattr(instance.get('dtstart').dt, 'isoformat') 
                    else str(instance.get('dtstart').dt) 
                    for instance in expanded_instances
                ])
                logger.debug(f"Expandierte Termine für '{summary}': {dates_str}")
            
            # Zum Kalender hinzufügen
            for instance in expanded_instances:
                new_cal.add_component(instance)
        
        # Kalender zurückgeben
        logger.info("Returning simplified calendar with expanded recurring events")
        return Response(new_cal.to_ical(), 
                      mimetype='text/calendar',
                      headers={'Content-Disposition': 'attachment; filename=simplified_calendar.ics'})
    
    except requests.RequestException as e:
        error_msg = f"Failed to download calendar: {str(e)}"
        logger.error(error_msg)
        return error_msg, 500
    except Exception as e:
        error_msg = f"Error processing calendar: {str(e)}"
        logger.exception(error_msg)
        return error_msg, 500