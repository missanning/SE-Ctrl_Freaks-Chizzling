import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Import centralized database connection
try:
    from db_connection import connect_db, get_db_path
except ImportError:
    # Fallback if db_connection is not available
    def connect_db():
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)
        db_path = os.path.join(base_path, "sales_inventory.db")
        return sqlite3.connect(db_path)
    
    def get_db_path():
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)
        return os.path.join(base_path, "sales_inventory.db")


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
