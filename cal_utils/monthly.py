from .base import (
    Calendar, Event, logger, datetime, pytz, re,
    rrulestr, parse,
    is_date_excluded, sanitize_rrule, create_instance_from_recurring
)

def manually_expand_monthly_byday(event, effective_start_date, effective_end_date, event_start_date, byday, 
                                 interval, excluded_dates, exceptions, current_year, current_month, start_year, start_month):
    """Behandelt die Expansion von monatlichen Terminen mit BYDAY-Regel"""
    import calendar
    uid = str(event.get('uid', ''))
    dtstart = event.get('dtstart').dt
    instances = []
    
    # Prüfen, ob der aktuelle Monat nach oder am Starttermin liegt
    current_first_day = datetime.date(current_year, current_month, 1)
    if current_first_day >= datetime.date(start_year, start_month, 1):
        # Intervall prüfen
        months_since_start = (current_year - start_year) * 12 + current_month - start_month
        if months_since_start % interval == 0:
            for day_expr in byday:
                day_expr = str(day_expr)
                
                # Parse BYDAY-Ausdruck (z.B. "2MO", "-1FR")
                match = re.match(r'([+-]?\d*)([A-Z]{2})', day_expr.upper())
                if match:
                    pos, day = match.groups()
                    
                    # Wochentag ermitteln
                    day_to_num = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}
                    weekday = day_to_num.get(day, 0)
                    
                    # Position ermitteln (0 = alle, 1 = erster, 2 = zweiter, -1 = letzter, etc.)
                    try:
                        if pos:
                            position = int(pos)
                        else:
                            position = 0  # Alle Vorkommen
                    except ValueError:
                        position = 0
                    
                    # Alle Tage des Monats durchgehen
                    cal = calendar.monthcalendar(current_year, current_month)
                    
                    # Alle Vorkommen des Wochentags sammeln
                    occurrences = []
                    for week in cal:
                        if week[weekday] != 0:
                            occurrences.append(week[weekday])
                    
                    # Bestimmtes Vorkommen auswählen
                    if position > 0 and position <= len(occurrences):
                        # Positives Vorkommen (1. Montag, 2. Freitag, etc.)
                        day_num = occurrences[position - 1]
                        process_monthly_day(day_num, current_year, current_month, event_start_date, effective_end_date, 
                                          excluded_dates, exceptions, event, uid, dtstart, instances)
                    elif position < 0 and abs(position) <= len(occurrences):
                        # Negatives Vorkommen (-1. Montag = letzter Montag, etc.)
                        day_num = occurrences[position]
                        process_monthly_day(day_num, current_year, current_month, event_start_date, effective_end_date, 
                                          excluded_dates, exceptions, event, uid, dtstart, instances)
                    elif position == 0:
                        # Alle Vorkommen
                        for day_num in occurrences:
                            process_monthly_day(day_num, current_year, current_month, event_start_date, effective_end_date, 
                                             excluded_dates, exceptions, event, uid, dtstart, instances)
    
    return instances

def process_monthly_day(day_num, current_year, current_month, event_start_date, effective_end_date, 
                      excluded_dates, exceptions, event, uid, dtstart, instances):
    """Verarbeitet einen bestimmten Tag eines Monats für monatliche Wiederholungen"""
    try:
        current_date = datetime.date(current_year, current_month, day_num)
        
        # Prüfen, ob das aktuelle Datum nach oder am Starttermin liegt
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
                        # Zeitzone beibehalten
                        if dtstart.tzinfo:
                            instance_dt = instance_dt.replace(tzinfo=dtstart.tzinfo)
                    else:
                        instance_dt = current_date
                    
                    instance = create_instance_from_recurring(event, instance_dt, uid)
                    instances.append(instance)
    except ValueError:
        # Ungültiges Datum - für einige Monate existieren bestimmte Tage nicht (z.B. 31. Februar)
        logger.debug(f"Überspringe ungültiges Datum: {current_year}-{current_month}-{day_num}")
        pass
