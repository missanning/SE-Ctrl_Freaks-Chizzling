import sqlite3

DB_NAME = "users.db"

# Connect to database
def connect():
    return sqlite3.connect(DB_NAME)

# Create table if not exists
def create_table():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Register user
def register_user(username, password):
    try:
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (username, password))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# Verify login
def login_user(username, password):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", 
                   (username, password))
    result = cursor.fetchone()
    conn.close()
    return result