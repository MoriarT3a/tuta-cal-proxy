from .base import (
    Calendar, Event, logger, datetime, pytz,
    rrulestr, parse,
    is_date_excluded, sanitize_rrule, create_instance_from_recurring
)
from .frequency import manually_expand_recurring_event

def expand_recurring_event(event, start_date, end_date, exceptions=None, excluded_dates=None):
    """Expandiert einen wiederkehrenden Termin zu einzelnen Terminen im angegebenen Zeitraum"""
    if exceptions is None:
        exceptions = []
    if excluded_dates is None:
        excluded_dates = []
    
    instances = []
    
    # Basisinformationen
    uid = str(event.get('uid', ''))
    dtstart = event.get('dtstart').dt
    
    # Das tatsächliche Startdatum des wiederkehrenden Termins
    event_start_date = dtstart.date() if isinstance(dtstart, datetime.datetime) else dtstart
    
    # Berücksichtige UNTIL-Datum aus RRULE (falls vorhanden)
    rrule_val = event.get('rrule', {})
    until_val = rrule_val.get('UNTIL', None)
    until_date = None
    
    if until_val:
        if isinstance(until_val, list) and until_val:
            until_val = until_val[0]
        
        if isinstance(until_val, datetime.datetime):
            until_date = until_val.date()
        elif isinstance(until_val, datetime.date):
            until_date = until_val
        elif isinstance(until_val, str):
            try:
                # Versuche das String-Datum zu parsen
                parsed_until = parse(until_val)
                until_date = parsed_until.date()
            except Exception as e:
                logger.warning(f"Konnte UNTIL-Datum nicht parsen: {until_val}, Fehler: {e}")
                
        # Zusätzliches Logging für das UNTIL-Datum
        logger.debug(f"UNTIL-Datum in RRULE gefunden: {until_date}")
    
    # Wenn das Startdatum des Events nach dem Ende des Zeitraums liegt, gibt es nichts zu expandieren
    if event_start_date > end_date:
        return []
    
    # Effektives Enddatum ist das frühere von end_date und until_date (wenn vorhanden)
    effective_end_date = end_date
    if until_date and until_date < end_date:
        effective_end_date = until_date
        logger.debug(f"UNTIL-Datum {until_date} ist früher als Ende des Zeitraums, verwende es als effektives Ende")
    
    # Korrektes Startdatum für die Expansion - das spätere von Event-Start und angefragetem Start
    effective_start_date = max(start_date, event_start_date)
    
    # Prüfe Zeitspanne - wenn Start und Ende sehr nah beieinander liegen
    # oder wir ein explizites UNTIL haben, verwende direkt die manuelle Expansion
    time_span = (effective_end_date - event_start_date).days
    
    if (until_date and time_span <= 7) or time_span <= 2:
        logger.debug(f"Kurze Zeitspanne ({time_span} Tage) oder definiertes UNTIL-Datum erkannt. Verwende manuelle Expansion.")
        instances = manually_expand_recurring_event(event, effective_start_date, effective_end_date, exceptions, excluded_dates)
        return instances
    
    try:
        # Versuche zuerst die automatische Expansion mit dateutil.rrule
        sanitized_rrule = sanitize_rrule(rrule_val)
        
        # Wenn keine gültigen Eigenschaften übrig sind, verwende manuelle Expansion
        if not sanitized_rrule:
            raise ValueError("Keine gültigen RRULE-Eigenschaften gefunden")
        
        # Wiederholungsregel als String erstellen
        rrule_parts = []
        for key, val in sanitized_rrule.items():
            if isinstance(val, list):
                val_str = ",".join(str(v) for v in val)
            else:
                val_str = str(val)
            rrule_parts.append(f"{key}={val_str}")
        
        # RRule-String erzeugen
        if isinstance(dtstart, datetime.datetime):
            dtstart_str = dtstart.strftime('%Y%m%dT%H%M%S')
            if dtstart.tzinfo:
                dtstart_str += 'Z' if dtstart.tzinfo == pytz.UTC else ''
        else:
            dtstart_str = dtstart.strftime('%Y%m%d')
        
        rrule_str = f"DTSTART:{dtstart_str}\nRRULE:{';'.join(rrule_parts)}"
        
        # Start- und Enddatum für Expansion
        if isinstance(dtstart, datetime.datetime):
            start_dt = datetime.datetime.combine(effective_start_date, datetime.time.min)
            if dtstart.tzinfo:
                start_dt = start_dt.replace(tzinfo=dtstart.tzinfo)
            
            end_dt = datetime.datetime.combine(effective_end_date, datetime.time.max)
            if dtstart.tzinfo:
                end_dt = end_dt.replace(tzinfo=dtstart.tzinfo)
        else:
            start_dt = effective_start_date
            end_dt = effective_end_date
        
        # Regeln expandieren
        rule = rrulestr(rrule_str, forceset=True)
        occurrences = list(rule.between(start_dt, end_dt, inc=True))
        
        # Log für Debugging
        logger.debug(f"Automatische Expansion: Gefunden {len(occurrences)} Termine zwischen {start_dt} und {end_dt}")
        
        if not occurrences:
            # Wenn keine Termine gefunden wurden, verwende manuelle Expansion
            logger.debug(f"Keine Termine mit automatischer Expansion gefunden. Verwende manuelle Expansion.")
            raise ValueError("Keine Termine mit automatischer Expansion gefunden")
        
        # Bei einer sehr geringen Anzahl von Terminen validieren wir doppelt mit manueller Expansion
        if 1 <= len(occurrences) <= 3 and until_date:
            logger.debug(f"Nur wenige Termine ({len(occurrences)}) mit UNTIL-Datum gefunden. Validiere mit manueller Expansion.")
            
            # Validieren mit manueller Expansion
            manual_instances = manually_expand_recurring_event(event, effective_start_date, effective_end_date, exceptions, excluded_dates)
            
            if len(manual_instances) != len(occurrences):
                logger.warning(f"Unterschied zwischen automatischer ({len(occurrences)}) und manueller ({len(manual_instances)}) Expansion. Verwende manuelle Ergebnisse.")
                return manual_instances
        
        # Instanzen verarbeiten
        for instance_dt in occurrences:
            # Datum für Filterung
            if isinstance(instance_dt, datetime.datetime):
                instance_date = instance_dt.date()
            else:
                instance_date = instance_dt
            
            # Prüfen, ob ausgeschlossen
            if is_date_excluded(instance_date, excluded_dates):
                continue
            
            # Prüfen, ob Ausnahme existiert
            exception_found = False
            for ex in exceptions:
                ex_date = ex.get('recurrence-id').dt
                if isinstance(ex_date, datetime.datetime):
                    ex_date = ex_date.date()
                
                if ex_date == instance_date:
                    # Ausnahme gefunden
                    exception_found = True
                    # Stelle sicher, dass die UID der Ausnahme korrekt ist
                    ex_uid = f"{uid}-{ex_date.isoformat()}"
                    ex['uid'] = ex_uid
                    instances.append(ex)
                    break
            
            if exception_found:
                continue
            
            # Neue Instanz erstellen
            instance = create_instance_from_recurring(event, instance_dt, uid)
            instances.append(instance)
    
    except Exception as e:
        logger.warning(f"Automatische Expansion fehlgeschlagen: {e}. Verwende manuelle Expansion.")
        
        # Wenn die automatische Expansion fehlschlägt, verwende die manuelle Expansion
        instances = manually_expand_recurring_event(event, effective_start_date, effective_end_date, exceptions, excluded_dates)
    
    return instances