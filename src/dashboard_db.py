import os
import sqlite3
from datetime import datetime, timedelta


def connect_db():
    db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
    return sqlite3.connect(db_path)


def get_date_range(period):
    """Return (date_from, date_to, title) for a given period string."""
    today = datetime.now()
    if period == "daily":
        d = today.strftime("%Y-%m-%d")
        return d, d, f"Today ({d})"
    elif period == "weekly":
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        df = monday.strftime("%Y-%m-%d")
        dt = sunday.strftime("%Y-%m-%d")
        return df, dt, f"This Week ({df} to {dt})"
    else:  # monthly
        first = today.replace(day=1)
        if today.month == 12:
            last = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        df = first.strftime("%Y-%m-%d")
        dt = last.strftime("%Y-%m-%d")
        return df, dt, f"This Month ({df} to {dt})"
