"""
Centralized database connection utility for Chizzling POS.
This ensures all modules use the same database path logic.
"""
import os
import sys
import sqlite3


def get_db_path():
    """
    Get the database path that works for both development and deployed executable.
    Returns the absolute path to sales_inventory.db
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        # Use the directory where the .exe is located
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as script - use src directory
        base_path = os.path.dirname(__file__)
    
    db_path = os.path.join(base_path, "sales_inventory.db")
    
    # Debug output (will show in console if running with console=True)
    print(f"[DB] Database path: {db_path}")
    print(f"[DB] Database exists: {os.path.exists(db_path)}")
    
    return db_path


def connect_db():
    """
    Create and return a connection to the database.
    This is the standard connection function used across all modules.
    """
    db_path = get_db_path()
    
    try:
        conn = sqlite3.connect(db_path)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        print(f"[DB ERROR] Failed to connect to database: {e}")
        raise
