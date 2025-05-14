from icalendar import Calendar, Event, vCalAddress, vText
import datetime
import pytz
import logging
import re
from dateutil.rrule import rrulestr
from dateutil.parser import parse

logger = logging.getLogger('ical-proxy')

# Standard RRULE-Eigenschaften nach RFC 5545
VALID_RRULE_PROPERTIES = {
    'FREQ', 'UNTIL', 'COUNT', 'INTERVAL', 'BYSECOND', 'BYMINUTE', 'BYHOUR', 
    'BYDAY', 'BYMONTHDAY', 'BYYEARDAY', 'BYWEEKNO', 'BYMONTH', 'BYSETPOS', 
    'WKST'
}

def get_date_string(dt):
    """Erzeugt einen konsistenten Datumsstring für ein Datum oder eine Uhrzeit"""
    if isinstance(dt, datetime.datetime):
        return dt.strftime('%Y%m%dT%H%M%S')
    elif isinstance(dt, datetime.date):
        return dt.strftime('%Y%m%d')
    else:
        return str(dt)

def is_date_excluded(instance_date, excluded_dates):
    """Prüft, ob ein Datum in der Liste der ausgeschlossenen Termine ist"""
    for excluded in excluded_dates:
        if isinstance(excluded, datetime.datetime) and excluded.date() == instance_date:
            return True
        elif isinstance(excluded, datetime.date) and excluded == instance_date:
            return True
    return False

def sanitize_rrule(rrule_val):
    """Bereinigt eine RRULE, indem ungültige Eigenschaften entfernt werden"""
    sanitized = {}
    
    for key, val in rrule_val.items():
        # Nur gültige Eigenschaften akzeptieren
        if key.upper() in VALID_RRULE_PROPERTIES:
            sanitized[key] = val
    
    return sanitized

def create_instance_from_recurring(event, instance_dt, uid_base, skip_properties=None):
    """Erstellt eine neue Instanz eines wiederkehrenden Termins für ein bestimmtes Datum"""
    if skip_properties is None:
        skip_properties = ['dtstart', 'dtend', 'uid', 'rrule', 'exdate', 'rdate', 'recurrence-id']
    
    instance = Event()
    
    # Eigenschaften vom Original übernehmen
    for attr, value in event.items():
        if attr.lower() not in skip_properties:
            instance.add(attr, value)
    
    # Original-Start- und Enddaten
    dtstart = event.get('dtstart').dt
    dtend = event.get('dtend').dt if 'dtend' in event else None
    
    # Dauer berechnen (für Endzeit)
    duration = None
    if dtend:
        if isinstance(dtstart, datetime.datetime) and isinstance(dtend, datetime.datetime):
            duration = dtend - dtstart
        elif isinstance(dtstart, datetime.date) and isinstance(dtend, datetime.date):
            duration = dtend - dtstart
    
    # Start- und Endzeit für die neue Instanz setzen
    if isinstance(dtstart, datetime.datetime):
        # Termin mit Uhrzeit
        if isinstance(instance_dt, datetime.datetime):
            # Zeitzone beibehalten
            if dtstart.tzinfo and not instance_dt.tzinfo:
                instance_dt = instance_dt.replace(tzinfo=dtstart.tzinfo)
            
            instance.add('dtstart', instance_dt)
            
            # Enddatum
            if duration:
                instance.add('dtend', instance_dt + duration)
        else:
            # Termin mit Datum, aber Originaltermin hat Uhrzeit
            new_dt = datetime.datetime.combine(instance_dt, dtstart.time())
            if dtstart.tzinfo:
                new_dt = new_dt.replace(tzinfo=dtstart.tzinfo)
            
            instance.add('dtstart', new_dt)
            
            # Enddatum
            if duration:
                instance.add('dtend', new_dt + duration)
    else:
        # Ganztägiger Termin
        if isinstance(instance_dt, datetime.datetime):
            instance.add('dtstart', instance_dt.date())
            
            # Enddatum
            if duration:
                end_date = (instance_dt + duration).date()
                instance.add('dtend', end_date)
        else:
            instance.add('dtstart', instance_dt)
            
            # Enddatum
            if duration:
                instance.add('dtend', instance_dt + duration)
    
    # Stabile UID generieren
    if isinstance(instance_dt, datetime.datetime):
        date_str = instance_dt.strftime('%Y%m%dT%H%M%S')
        if instance_dt.tzinfo:
            date_str += 'Z' if instance_dt.tzinfo == pytz.UTC else ''
    else:
        date_str = instance_dt.strftime('%Y%m%d')
    
    # UID generieren, die garantiert für jeden Termin einzigartig ist
    stable_uid = f"{uid_base}-{date_str}"
    instance.add('uid', stable_uid)
    
    # Für Tuta: Stelle sicher, dass DTSTAMP vorhanden ist (wird manchmal benötigt)
    if 'dtstamp' not in instance:
        now = datetime.datetime.now(pytz.UTC)
        instance.add('dtstamp', now)
    
    return instance

def sanitize_calendar(cal):
    """Bereinigt einen Kalender, indem bestimmte Komponenten entfernt werden"""
    new_cal = Calendar()
    new_cal.add('prodid', '-//ICS Calendar Proxy//EN')
    new_cal.add('version', '2.0')
    
    # Wenn das Original eine METHOD hat, übernehmen
    if 'method' in cal:
        new_cal.add('method', cal['method'])
    else:
        new_cal.add('method', 'PUBLISH')
    
    # Timezone-Komponenten übernehmen
    for component in cal.walk('VTIMEZONE'):
        new_cal.add_component(component)
    
    # Stelle sicher, dass der Kalender für Tuta kompatible Attribute hat
    if 'calscale' not in new_cal and 'calscale' in cal:
        new_cal.add('calscale', cal['calscale'])
    
    return new_cal

def extract_excluded_dates(event):
    """Extrahiert die ausgeschlossenen Termine eines Events"""
    excluded_dates = []
    
    if event.get('exdate'):
        exdate_list = event.get('exdate')
        if not isinstance(exdate_list, list):
            exdate_list = [exdate_list]
        
        for exdate in exdate_list:
            if hasattr(exdate, 'dts'):
                for dt in exdate.dts:
                    excluded_dates.append(dt.dt)
            else:
                excluded_dates.append(exdate)
    
    return excluded_dates
