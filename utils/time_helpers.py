from datetime import time, timedelta

def week_day_number(day_name):
    return ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].index(day_name)

def timedelta_to_time(value):
    """Normalize MySQL TIME values returned as timedelta to datetime.time.

    mysql.connector may represent TIME columns as timedelta; datetime.time
    values are passed through unchanged.
    """
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        total = int(value.total_seconds()) % 86400
        return time(total // 3600, (total % 3600) // 60, total % 60)
    raise TypeError(f"Expected datetime.time or timedelta, got {type(value).__name__}")
