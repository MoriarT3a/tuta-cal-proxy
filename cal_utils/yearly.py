def expand_yearly(event, effective_start_date, effective_end_date, interval, excluded_dates, exceptions):
    """Expandiert jährliche wiederkehrende Termine"""
    from .base import (
        datetime, is_date_excluded, create_instance_from_recurring
    )
    
    instances = []
    uid = str(event.get('uid', ''))
    dtstart = event.get('dtstart').dt
    event_start_date = dtstart.date() if isinstance(dtstart, datetime.datetime) else dtstart
    
    # Jährliche Wiederholung
    # BYMONTH und BYMONTHDAY prüfen
    rrule = event.get('rrule', {})
    bymonth = rrule.get('BYMONTH', [])
    if not isinstance(bymonth, list):
        bymonth = [bymonth]
    
    bymonthday = rrule.get('BYMONTHDAY', [])
    if not isinstance(bymonthday, list):
        bymonthday = [bymonthday]
    
    # Wenn keine dieser Eigenschaften gesetzt ist, den Monat und Tag vom Starttermin verwenden
    if not bymonth:
        bymonth = [event_start_date.month]
    
    if not bymonthday:
        bymonthday = [event_start_date.day]
    
    # Startjahr
    start_year = event_start_date.year
    
    # Für jedes Jahr innerhalb des Zeitraums
    for year in range(effective_start_date.year, effective_end_date.year + 1):
        # Prüfen, ob das aktuelle Jahr nach oder am Startjahr liegt
        if year >= start_year:
            # Intervall prüfen
            years_since_start = year - start_year
            if years_since_start % interval == 0:
                for month in bymonth:
                    try:
                        month_num = int(month)
                        for day in bymonthday:
                            try:
                                day_num = int(day)
                                current_date = datetime.date(year, month_num, day_num)
                                
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
                                # Ungültiges Datum
                                pass
                    except ValueError:
                        # Ungültiger Monat
                        pass
    
    return instances