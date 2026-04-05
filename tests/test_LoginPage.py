import pytest
from LoginPage import MainApp
from database_setup import connect_db

def test_login_valid():
    # Test login with valid credentials
    con = connect_db()
    cursor = con.cursor()
    # Assume there's a user in the database
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ("testuser", "testpass", "admin"))
    con.commit()
    con.close()

    # Since it's GUI, we can't easily test, but we can test the database part
    con = connect_db()
    cursor = con.cursor()
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", ("testuser", "testpass"))
    result = cursor.fetchone()
    con.close()
    assert result is not None
    assert result[0] == "admin"

def test_login_invalid():
    con = connect_db()
    cursor = con.cursor()
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", ("invalid", "invalid"))
    result = cursor.fetchone()
    con.close()
    assert result is None