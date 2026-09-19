from datetime import datetime, time, timedelta


def civil_end(day, tz):
    return datetime.combine(day + timedelta(days=1), time.min, tz)
