from .base import (
    Calendar, Event, logger, datetime, pytz, re,
    rrulestr, parse,
    is_date_excluded, sanitize_rrule, create_instance_from_recurring
)
from .monthly import manually_expand_monthly_byday
from .yearly import expand_yearly

def manually_expand_recurring_event(event, start_date, end_date, exceptions=None, excluded_dates=None):
    """Manuelle Expansion von wiederkehrenden Terminen, wenn die automatische Expansion fehlschlägt"""
    if exceptions is None:
        exceptions = []
    if excluded_dates is None:
        excluded_dates = []
    
    instances = []
    uid = str(event.get('uid', ''))
    dtstart = event.get('dtstart').dt
    
    # UNTIL-Datum aus RRULE extrahieren und beachten
    rrule = event.get('rrule', {})
    until_val = rrule.get('UNTIL', None)
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
    
    # Effektives Enddatum ist das frühere von end_date und until_date (wenn vorhanden)
    effective_end_date = end_date
    if until_date and until_date < end_date:
        effective_end_date = until_date
        logger.debug(f"UNTIL-Datum {until_date} ist früher als Ende des Zeitraums, verwende es als effektives Ende")
    
    # Frequenz und Intervall ermitteln
    freq_val = rrule.get('FREQ', ['DAILY'])
    freq = str(freq_val[0] if isinstance(freq_val, list) else freq_val).upper()
    
    interval_val = rrule.get('INTERVAL', [1])
    try:
        interval = int(interval_val[0] if isinstance(interval_val, list) else interval_val)
    except (ValueError, TypeError):
        interval = 1
    
    # Das tatsächliche Startdatum des wiederkehrenden Termins
    event_start_date = dtstart.date() if isinstance(dtstart, datetime.datetime) else dtstart
    
    # Korrektes Startdatum für die Expansion - das spätere von Event-Start und angefragetem Start
    effective_start_date = max(start_date, event_start_date)
    
    # Für Termine mit sehr kurzen Zeiträumen (z.B. 2 Tage) spezielle Behandlung
    time_span = (effective_end_date - event_start_date).days + 1  # +1 weil wir beide Tage mitzählen
    
    # Wenn der Zeitraum sehr kurz ist (z.B. 1-3 Tage)
    if time_span <= 7 and freq == 'WEEKLY' and until_date and 'BYDAY' in rrule:
        logger.debug(f"Kurzer Zeitraum mit UNTIL und BYDAY erkannt: {time_span} Tage")
        
        bydays = rrule.get('BYDAY', [])
        if not isinstance(bydays, list):
            bydays = [bydays]
        
        day_to_num = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}
        weekdays = []
        for day in bydays:
            day_str = str(day).upper()
            day_code = re.search(r'(?:[+-]?\d*)([A-Z]{2})', day_str)
            if day_code and day_code.group(1) in day_to_num:
                weekdays.append(day_to_num[day_code.group(1)])
        
        # Nun generieren wir nur Termine innerhalb des genauen Zeitraums
        logger.debug(f"Spezialbehandlung: Prüfe Tage zwischen {effective_start_date} und {effective_end_date} an Wochentagen {weekdays}")
        
        # Taggenau durch den Zeitraum iterieren
        current_date = effective_start_date
        while current_date <= effective_end_date:
            # Nur Termine an den richtigen Wochentagen erzeugen
            if current_date.weekday() in weekdays:
                logger.debug(f"Prüfe Tag {current_date} (Wochentag {current_date.weekday()})")
                
                # Prüfen, ob der Tag ausgeschlossen ist
                if not is_date_excluded(current_date, excluded_dates):
                    # Prüfen, ob es eine Ausnahme gibt
                    exception_found = False
                    for ex in exceptions:
                        ex_date = ex.get('recurrence-id').dt
                        if isinstance(ex_date, datetime.datetime):
                            ex_date = ex_date.date()
                        if ex_date == current_date:
                            exception_found = True
                            # Stelle sicher, dass die UID der Ausnahme korrekt ist
                            ex_uid = f"{uid}-{ex_date.isoformat()}"
                            ex['uid'] = ex_uid
                            instances.append(ex)
                            break
                    
                    if not exception_found:
                        # Neue Instanz erstellen
                        if isinstance(dtstart, datetime.datetime):
                            time_of_day = dtstart.time()
                            instance_dt = datetime.datetime.combine(current_date, time_of_day)
                            if dtstart.tzinfo:
                                instance_dt = instance_dt.replace(tzinfo=dtstart.tzinfo)
                        else:
                            instance_dt = current_date
                        
                        instance = create_instance_from_recurring(event, instance_dt, uid)
                        instances.append(instance)
                        logger.debug(f"Instanz erstellt für {current_date}")
            
            current_date += datetime.timedelta(days=1)
        
        return instances
    
    # Normale Expansion basierend auf Frequenz für andere Fälle
    if freq == 'DAILY':
        instances = expand_daily(event, effective_start_date, effective_end_date, interval, excluded_dates, exceptions)
    elif freq == 'WEEKLY':
        instances = expand_weekly(event, effective_start_date, effective_end_date, interval, excluded_dates, exceptions)
    elif freq == 'MONTHLY':
        instances = expand_monthly(event, effective_start_date, effective_end_date, interval, excluded_dates, exceptions)
    elif freq == 'YEARLY':
        instances = expand_yearly(event, effective_start_date, effective_end_date, interval, excluded_dates, exceptions)
    
    return instances

def expand_daily(event, effective_start_date, effective_end_date, interval, excluded_dates, exceptions):
    """Expandiert tägliche wiederkehrende Termine"""
    instances = []
    uid = str(event.get('uid', ''))
    dtstart = event.get('dtstart').dt
    event_start_date = dtstart.date() if isinstance(dtstart, datetime.datetime) else dtstart
    
    # Tägliche Wiederholung
    current_date = effective_start_date
    while current_date <= effective_end_date:
        # Prüfen, ob das aktuelle Datum nach oder am Starttermin liegt
        if current_date >= event_start_date:
            # Intervall prüfen
            days_since_start = (current_date - event_start_date).days
            if days_since_start % interval == 0:
                if not is_date_excluded(current_date, excluded_dates):
                    # Ausnahme prüfen
                    exception_found = False
                    for ex in exceptions:
                        ex_date = ex.get('recurrence-id').dt
                        if isinstance(ex_date, datetime.datetime):
                            ex_date = ex_date.date()
                        if ex_date == current_date:
                            exception_found = True
                            # Stelle sicher, dass die UID der Ausnahme korrekt ist
                            ex_uid = f"{uid}-{ex_date.isoformat()}"
                            ex['uid'] = ex_uid
                            instances.append(ex)
                            break
                    
                    if not exception_found:
                        # Neue Instanz erstellen
                        if isinstance(dtstart, datetime.datetime):
                            time_of_day = dtstart.time()
                            instance_dt = datetime.datetime.combine(current_date, time_of_day)
                            if dtstart.tzinfo:
                                instance_dt = instance_dt.replace(tzinfo=dtstart.tzinfo)
                        else:
                            instance_dt = current_date
                        
                        instance = create_instance_from_recurring(event, instance_dt, uid)
                        instances.append(instance)
        
        current_date += datetime.timedelta(days=1)
    
    return instances

def expand_weekly(event, effective_start_date, effective_end_date, interval, excluded_dates, exceptions):
    """Expandiert wöchentliche wiederkehrende Termine"""
    instances = []
    uid = str(event.get('uid', ''))
    dtstart = event.get('dtstart').dt
    event_start_date = dtstart.date() if isinstance(dtstart, datetime.datetime) else dtstart
    
    # Wöchentliche Wiederholung
    # BYDAY herausfinden
    rrule = event.get('rrule', {})
    bydays = rrule.get('BYDAY', [])
    if not isinstance(bydays, list):
        bydays = [bydays]
    
    if not bydays:
        # Wenn kein BYDAY, den Wochentag des Starttermins verwenden
        if isinstance(dtstart, datetime.datetime):
            start_weekday = dtstart.date().weekday()
        else:
            start_weekday = dtstart.weekday()
        
        day_map = {0: 'MO', 1: 'TU', 2: 'WE', 3: 'TH', 4: 'FR', 5: 'SA', 6: 'SU'}
        bydays = [day_map[start_weekday]]
    
    # Wochentage in numerische Darstellung umwandeln
    day_to_num = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}
    weekdays = []
    for day in bydays:
        day_str = str(day).upper()
        # Extrahiere nur die Wochentagsbezeichnung (ignoriere mögliche Positionen wie 1MO, -1FR)
        day_code = re.search(r'(?:[+-]?\d*)([A-Z]{2})', day_str)
        if day_code and day_code.group(1) in day_to_num:
            weekdays.append(day_to_num[day_code.group(1)])
    
    # Wochenstart basierend auf WKST
    wkst_val = rrule.get('WKST', ['MO'])
    wkst = str(wkst_val[0] if isinstance(wkst_val, list) else wkst_val).upper()[:2]
    week_start = day_to_num.get(wkst, 0)  # Standard ist Montag
    
    # Berechnung der ersten Woche
    # Finde den ersten Tag der Woche von dtstart aus
    if isinstance(dtstart, datetime.datetime):
        first_day_offset = dtstart.date().weekday() - week_start
    else:
        first_day_offset = dtstart.weekday() - week_start
    
    if first_day_offset < 0:
        first_day_offset += 7
    
    first_day_of_first_week = event_start_date - datetime.timedelta(days=first_day_offset)
    
    # Zum Startdatum der Expansion gehen
    current_date = effective_start_date
    
    # Für jeden Tag innerhalb des Zeitraums
    while current_date <= effective_end_date:
        # Prüfen, ob der aktuelle Tag ein passender Wochentag ist
        if current_date.weekday() in weekdays:
            # Prüfen, ob das aktuelle Datum nach oder am Starttermin liegt
            if current_date >= event_start_date:
                # Intervall prüfen (nur alle X Wochen)
                days_diff = (current_date - first_day_of_first_week).days
                weeks_diff = days_diff // 7
                
                if weeks_diff % interval == 0:
                    if not is_date_excluded(current_date, excluded_dates):
                        # Ausnahme prüfen
                        exception_found = False
                        for ex in exceptions:
                            ex_date = ex.get('recurrence-id').dt
                            if isinstance(ex_date, datetime.datetime):
                                ex_date = ex_date.date()
                            if ex_date == current_date:
                                exception_found = True
                                # Stelle sicher, dass die UID der Ausnahme korrekt ist
                                ex_uid = f"{uid}-{ex_date.isoformat()}"
                                ex['uid'] = ex_uid
                                instances.append(ex)
                                break
                        
                        if not exception_found:
                            # Neue Instanz erstellen
                            if isinstance(dtstart, datetime.datetime):
                                time_of_day = dtstart.time()
                                instance_dt = datetime.datetime.combine(current_date, time_of_day)
                                if dtstart.tzinfo:
                                    instance_dt = instance_dt.replace(tzinfo=dtstart.tzinfo)
                            else:
                                instance_dt = current_date
                            
                            instance = create_instance_from_recurring(event, instance_dt, uid)
                            instances.append(instance)
        
        current_date += datetime.timedelta(days=1)
    
    return instances

def expand_monthly(event, effective_start_date, effective_end_date, interval, excluded_dates, exceptions):
    """Expandiert monatliche wiederkehrende Termine"""
    instances = []
    uid = str(event.get('uid', ''))
    dtstart = event.get('dtstart').dt
    event_start_date = dtstart.date() if isinstance(dtstart, datetime.datetime) else dtstart
    
    # Monatliche Wiederholung
    # BYMONTHDAY oder BYDAY prüfen
    rrule = event.get('rrule', {})
    bymonthday = rrule.get('BYMONTHDAY', [])
    if not isinstance(bymonthday, list):
        bymonthday = [bymonthday]
    
    byday = rrule.get('BYDAY', [])
    if not isinstance(byday, list):
        byday = [byday]
    
    # Wenn keine dieser Eigenschaften gesetzt ist, den Tag des Monats vom Starttermin verwenden
    if not bymonthday and not byday:
        if isinstance(dtstart, datetime.datetime):
            bymonthday = [dtstart.date().day]
        else:
            bymonthday = [dtstart.day]
    
    # Startmonat und -jahr
    start_month = event_start_date.month
    start_year = event_start_date.year
    
    # Für jeden Monat innerhalb des Zeitraums
    current_year = effective_start_date.year
    current_month = effective_start_date.month
    end_year = effective_end_date.year
    end_month = effective_end_date.month
    
    while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
        # Prüfen, ob der aktuelle Monat nach oder am Starttermin liegt
        current_first_day = datetime.date(current_year, current_month, 1)
        if current_first_day >= datetime.date(start_year, start_month, 1):
            # Intervall prüfen
            months_since_start = (current_year - start_year) * 12 + current_month - start_month
            if months_since_start % interval == 0:
                # Tage für diesen Monat generieren
                if bymonthday:
                    # BYMONTHDAY: Bestimmte Tage des Monats
                    for day in bymonthday:
                        try:
                            day_num = int(day)
                            current_date = datetime.date(current_year, current_month, day_num)
                            
                            # Prüfen, ob das aktuelle Datum nach oder am Starttermin liegt und vor oder am Endtermin
                            if current_date >= event_start_date and current_date <= effective_end_date:
                                if not is_date_excluded(current_date, excluded_dates):
                                    # Ausnahme prüfen
                                    exception_found = False
                                    for ex in exceptions:
                                        ex_date = ex.get('recurrence-id').dt
                                        if isinstance(ex_date, datetime.datetime):
                                            ex_date = ex_date.date()
                                        if ex_date == current_date:
                                            exception_found = True
                                            # Stelle sicher, dass die UID der Ausnahme korrekt ist
                                            ex_uid = f"{uid}-{ex_date.isoformat()}"
                                            ex['uid'] = ex_uid
                                            instances.append(ex)
                                            break
                                    
                                    if not exception_found:
                                        # Neue Instanz erstellen
                                        if isinstance(dtstart, datetime.datetime):
                                            time_of_day = dtstart.time()
                                            instance_dt = datetime.datetime.combine(current_date, time_of_day)
                                            if dtstart.tzinfo:
                                                instance_dt = instance_dt.replace(tzinfo=dtstart.tzinfo)
                                        else:
                                            instance_dt = current_date
                                        
                                        instance = create_instance_from_recurring(event, instance_dt, uid)
                                        instances.append(instance)
                        except ValueError:
                            # Ungültiges Datum (z.B. 31. Februar)
                            pass
                
                elif byday:
                    # Verwende die separate Funktion zur Bearbeitung von BYDAY
                    new_instances = manually_expand_monthly_byday(
                        event, effective_start_date, effective_end_date, event_start_date, 
                        byday, interval, excluded_dates, exceptions, 
                        current_year, current_month, start_year, start_month
                    )
                    instances.extend(new_instances)
        
        # Zum nächsten Monat wechseln
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    
    return instances