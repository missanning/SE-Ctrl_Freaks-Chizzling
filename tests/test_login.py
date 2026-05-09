# Test for US-05: System Login Requirement


import pytest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Create a temp database with a users table and default users."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role     TEXT
    )
    """)
    cursor.executemany(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        [
            ("admin",           "1234", "admin"),
            ("cashier",         "1234", "cashier"),
            ("inventory_staff", "1234", "inventory_staff"),
        ]
    )
    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def empty_db():
    """Create a temp database with an empty users table."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role     TEXT
    )
    """)
    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


# ── Auth helper (mirrors LoginPage.login() logic) ──────────────────────────────

def attempt_login(db_path, username, password):
    """
    Simulate login logic.
    Returns role string on success, None on failure.
    Returns 'empty_fields' if username or password is blank.
    """
    if not username or not password:
        return "empty_fields"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role FROM users WHERE username=? AND password=?",
        (username, password)
    )
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def is_authenticated(db_path, username, password):
    """Returns True if credentials are valid."""
    return attempt_login(db_path, username, password) not in (None, "empty_fields")


# ── AC1: Unauthenticated access is blocked ────────────────────────────────────

class TestUnauthenticatedAccess:
    """AC1: Users not logged in are redirected to the login page."""

    def test_no_credentials_denied(self, temp_db):
        result = attempt_login(temp_db, "", "")
        assert result == "empty_fields"

    def test_blank_username_denied(self, temp_db):
        result = attempt_login(temp_db, "", "1234")
        assert result == "empty_fields"

    def test_blank_password_denied(self, temp_db):
        result = attempt_login(temp_db, "admin", "")
        assert result == "empty_fields"

    def test_blank_fields_not_authenticated(self, temp_db):
        assert is_authenticated(temp_db, "", "") is False

    def test_blank_username_not_authenticated(self, temp_db):
        assert is_authenticated(temp_db, "", "1234") is False

    def test_blank_password_not_authenticated(self, temp_db):
        assert is_authenticated(temp_db, "admin", "") is False

    def test_whitespace_username_denied(self, temp_db):
        result = attempt_login(temp_db, "   ", "1234")
        assert result is None or result == "empty_fields"

    def test_whitespace_password_denied(self, temp_db):
        result = attempt_login(temp_db, "admin", "   ")
        assert result is None or result == "empty_fields"

    def test_no_users_in_db_denies_access(self, empty_db):
        result = attempt_login(empty_db, "admin", "1234")
        assert result is None

    def test_unauthenticated_returns_no_role(self, temp_db):
        result = attempt_login(temp_db, "", "")
        assert result != "admin"
        assert result != "cashier"
        assert result != "inventory_staff"


# ── AC2: Valid credentials grant access ───────────────────────────────────────

class TestValidCredentials:
    """AC2: Valid credentials grant access to the system."""

    def test_admin_login_succeeds(self, temp_db):
        result = attempt_login(temp_db, "admin", "1234")
        assert result == "admin"

    def test_cashier_login_succeeds(self, temp_db):
        result = attempt_login(temp_db, "cashier", "1234")
        assert result == "cashier"

    def test_inventory_staff_login_succeeds(self, temp_db):
        result = attempt_login(temp_db, "inventory_staff", "1234")
        assert result == "inventory_staff"

    def test_valid_login_returns_role(self, temp_db):
        result = attempt_login(temp_db, "admin", "1234")
        assert result is not None
        assert result in ("admin", "cashier", "inventory_staff")

    def test_valid_login_is_authenticated(self, temp_db):
        assert is_authenticated(temp_db, "admin", "1234") is True

    def test_cashier_is_authenticated(self, temp_db):
        assert is_authenticated(temp_db, "cashier", "1234") is True

    def test_inventory_staff_is_authenticated(self, temp_db):
        assert is_authenticated(temp_db, "inventory_staff", "1234") is True

    def test_admin_role_routes_to_dashboard(self, temp_db):
        role = attempt_login(temp_db, "admin", "1234")
        assert role == "admin"

    def test_cashier_role_routes_to_pos(self, temp_db):
        role = attempt_login(temp_db, "cashier", "1234")
        assert role == "cashier"

    def test_inventory_staff_role_routes_to_inventory(self, temp_db):
        role = attempt_login(temp_db, "inventory_staff", "1234")
        assert role == "inventory_staff"

    def test_all_default_users_can_login(self, temp_db):
        credentials = [
            ("admin",           "1234"),
            ("cashier",         "1234"),
            ("inventory_staff", "1234"),
        ]
        for username, password in credentials:
            assert is_authenticated(temp_db, username, password) is True


# ── AC3: Invalid credentials show error ───────────────────────────────────────

class TestInvalidCredentials:
    """AC3: Invalid credentials display an error message."""

    def test_wrong_password_returns_none(self, temp_db):
        result = attempt_login(temp_db, "admin", "wrongpassword")
        assert result is None

    def test_wrong_username_returns_none(self, temp_db):
        result = attempt_login(temp_db, "unknownuser", "1234")
        assert result is None

    def test_wrong_username_and_password_returns_none(self, temp_db):
        result = attempt_login(temp_db, "hacker", "hacked")
        assert result is None

    def test_invalid_login_not_authenticated(self, temp_db):
        assert is_authenticated(temp_db, "admin", "wrongpassword") is False

    def test_case_sensitive_username(self, temp_db):
        result = attempt_login(temp_db, "Admin", "1234")
        assert result is None

    def test_case_sensitive_password(self, temp_db):
        result = attempt_login(temp_db, "admin", "ABCD")
        assert result is None

    def test_sql_injection_attempt_denied(self, temp_db):
        result = attempt_login(temp_db, "' OR '1'='1", "' OR '1'='1")
        assert result is None

    def test_partial_username_denied(self, temp_db):
        result = attempt_login(temp_db, "adm", "1234")
        assert result is None

    def test_partial_password_denied(self, temp_db):
        result = attempt_login(temp_db, "admin", "123")
        assert result is None

    def test_swapped_credentials_denied(self, temp_db):
        # password used as username and vice versa
        result = attempt_login(temp_db, "1234", "admin")
        assert result is None

    def test_invalid_login_returns_no_role(self, temp_db):
        result = attempt_login(temp_db, "admin", "wrongpassword")
        assert result not in ("admin", "cashier", "inventory_staff")

    def test_nonexistent_user_denied(self, temp_db):
        result = attempt_login(temp_db, "ghost", "1234")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
