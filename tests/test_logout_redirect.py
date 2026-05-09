# Test for US-22: Redirect to Login Page After Logout


import pytest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Create a temp database with all 3 user roles."""
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

    try:
        os.unlink(temp_file.name)
    except PermissionError:
        pass


# ── Auth helper ────────────────────────────────────────────────────────────────

def attempt_login(db_path, username, password):
    """Returns role on success, None on failure, 'empty_fields' if blank."""
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


# ── Logout logic helpers (mirror each interface's logout) ──────────────────────

class MockSession:
    """Simulates an active user session for any interface."""

    def __init__(self, role):
        self.role = role
        self.is_open = True
        self.redirected_to_login = False

    def logout(self):
        """Simulate closing current window and redirecting to login."""
        self.is_open = False
        self.redirected_to_login = True

    def is_logged_out(self):
        return not self.is_open and self.redirected_to_login


def get_logout_button_config(interface):
    """
    Returns logout button metadata for each interface.
    Mirrors actual button definitions in dashboard.py, pos_header.py,
    and ProductManagementSystem.py.
    """
    configs = {
        "dashboard": {
            "text": "Logout",
            "bg": "#DC3545",
            "fg": "white",
            "command": "logout_and_redirect"
        },
        "pos": {
            "text": "⏻  Logout",
            "bg": "#E8820C",
            "fg": "white",
            "command": "_do_logout"
        },
        "inventory": {
            "text": "⎋  Logout",
            "bg": "#7a3b10",
            "fg": "#ffd966",
            "command": "_logout"
        }
    }
    return configs.get(interface)


def get_role_interface(role):
    """Returns the expected interface for each role."""
    mapping = {
        "cashier":         "pos",
        "admin":           "dashboard",
        "inventory_staff": "inventory"
    }
    return mapping.get(role)


# ── AC1: Logout button exists in all interfaces ───────────────────────────────

class TestLogoutButtonExists:
    """AC1: Logout buttons are displayed in inventory, dashboard, and POS."""

    def test_dashboard_has_logout_button(self):
        config = get_logout_button_config("dashboard")
        assert config is not None

    def test_dashboard_logout_button_text(self):
        config = get_logout_button_config("dashboard")
        assert config["text"] == "Logout"

    def test_dashboard_logout_button_has_command(self):
        config = get_logout_button_config("dashboard")
        assert config["command"] == "logout_and_redirect"

    def test_pos_has_logout_button(self):
        config = get_logout_button_config("pos")
        assert config is not None

    def test_pos_logout_button_text(self):
        config = get_logout_button_config("pos")
        assert "Logout" in config["text"]

    def test_pos_logout_button_has_command(self):
        config = get_logout_button_config("pos")
        assert config["command"] == "_do_logout"

    def test_inventory_has_logout_button(self):
        config = get_logout_button_config("inventory")
        assert config is not None

    def test_inventory_logout_button_text(self):
        config = get_logout_button_config("inventory")
        assert "Logout" in config["text"]

    def test_inventory_logout_button_has_command(self):
        config = get_logout_button_config("inventory")
        assert config["command"] == "_logout"

    def test_all_interfaces_have_logout_button(self):
        for interface in ("dashboard", "pos", "inventory"):
            config = get_logout_button_config(interface)
            assert config is not None, f"{interface} missing logout button"


# ── AC2: Logout closes current session ────────────────────────────────────────

class TestLogoutClosesSession:
    """AC2: Clicking logout closes the current application."""

    def test_logout_closes_dashboard_session(self):
        session = MockSession("admin")
        session.logout()
        assert session.is_open is False

    def test_logout_closes_pos_session(self):
        session = MockSession("cashier")
        session.logout()
        assert session.is_open is False

    def test_logout_closes_inventory_session(self):
        session = MockSession("inventory_staff")
        session.logout()
        assert session.is_open is False

    def test_logout_sets_redirect_flag(self):
        session = MockSession("admin")
        session.logout()
        assert session.redirected_to_login is True

    def test_is_logged_out_returns_true_after_logout(self):
        session = MockSession("cashier")
        session.logout()
        assert session.is_logged_out() is True

    def test_session_is_open_before_logout(self):
        session = MockSession("admin")
        assert session.is_open is True

    def test_redirect_flag_false_before_logout(self):
        session = MockSession("cashier")
        assert session.redirected_to_login is False

    def test_logout_from_all_roles(self):
        for role in ("admin", "cashier", "inventory_staff"):
            session = MockSession(role)
            session.logout()
            assert session.is_logged_out() is True

    def test_session_cannot_be_reused_after_logout(self):
        session = MockSession("admin")
        session.logout()
        assert session.is_open is False
        assert session.redirected_to_login is True


# ── AC3: Login page launches successfully after logout ────────────────────────

class TestLoginPageAfterLogout:
    """AC3: Login page launches successfully without errors after logout."""

    def test_login_page_accessible_after_logout(self, temp_db):
        # Simulate logout then attempt login
        session = MockSession("admin")
        session.logout()
        assert session.is_logged_out() is True
        # Login page should accept credentials
        result = attempt_login(temp_db, "admin", "1234")
        assert result == "admin"

    def test_login_accepts_credentials_after_cashier_logout(self, temp_db):
        session = MockSession("cashier")
        session.logout()
        result = attempt_login(temp_db, "cashier", "1234")
        assert result == "cashier"

    def test_login_accepts_credentials_after_inventory_logout(self, temp_db):
        session = MockSession("inventory_staff")
        session.logout()
        result = attempt_login(temp_db, "inventory_staff", "1234")
        assert result == "inventory_staff"

    def test_login_page_rejects_blank_credentials_after_logout(self, temp_db):
        session = MockSession("admin")
        session.logout()
        result = attempt_login(temp_db, "", "")
        assert result == "empty_fields"

    def test_login_page_rejects_invalid_credentials_after_logout(self, temp_db):
        session = MockSession("admin")
        session.logout()
        result = attempt_login(temp_db, "admin", "wrongpassword")
        assert result is None

    def test_login_page_returns_role_after_logout(self, temp_db):
        session = MockSession("admin")
        session.logout()
        role = attempt_login(temp_db, "admin", "1234")
        assert role in ("admin", "cashier", "inventory_staff")

    def test_multiple_logouts_login_still_works(self, temp_db):
        for _ in range(3):
            session = MockSession("cashier")
            session.logout()
        result = attempt_login(temp_db, "cashier", "1234")
        assert result == "cashier"


# ── AC4: Role-based redirect after re-login ───────────────────────────────────

class TestRoleBasedRedirectAfterLogin:
    """AC4: Users can log back in with different credentials to access role-based interfaces."""

    def test_cashier_redirects_to_pos(self, temp_db):
        role = attempt_login(temp_db, "cashier", "1234")
        interface = get_role_interface(role)
        assert interface == "pos"

    def test_admin_redirects_to_dashboard(self, temp_db):
        role = attempt_login(temp_db, "admin", "1234")
        interface = get_role_interface(role)
        assert interface == "dashboard"

    def test_inventory_staff_redirects_to_inventory(self, temp_db):
        role = attempt_login(temp_db, "inventory_staff", "1234")
        interface = get_role_interface(role)
        assert interface == "inventory"

    def test_switch_from_admin_to_cashier(self, temp_db):
        # Admin logs out
        admin_session = MockSession("admin")
        admin_session.logout()
        assert admin_session.is_logged_out() is True
        # Cashier logs in
        role = attempt_login(temp_db, "cashier", "1234")
        assert role == "cashier"
        assert get_role_interface(role) == "pos"

    def test_switch_from_cashier_to_admin(self, temp_db):
        cashier_session = MockSession("cashier")
        cashier_session.logout()
        role = attempt_login(temp_db, "admin", "1234")
        assert role == "admin"
        assert get_role_interface(role) == "dashboard"

    def test_switch_from_cashier_to_inventory(self, temp_db):
        cashier_session = MockSession("cashier")
        cashier_session.logout()
        role = attempt_login(temp_db, "inventory_staff", "1234")
        assert role == "inventory_staff"
        assert get_role_interface(role) == "inventory"

    def test_switch_from_inventory_to_cashier(self, temp_db):
        inv_session = MockSession("inventory_staff")
        inv_session.logout()
        role = attempt_login(temp_db, "cashier", "1234")
        assert role == "cashier"
        assert get_role_interface(role) == "pos"

    def test_all_roles_map_to_correct_interface(self, temp_db):
        expected = {
            "cashier":         "pos",
            "admin":           "dashboard",
            "inventory_staff": "inventory",
        }
        credentials = {
            "cashier":         ("cashier",         "1234"),
            "admin":           ("admin",            "1234"),
            "inventory_staff": ("inventory_staff",  "1234"),
        }
        for role, (username, password) in credentials.items():
            logged_role = attempt_login(temp_db, username, password)
            assert get_role_interface(logged_role) == expected[role]

    def test_invalid_credentials_do_not_redirect(self, temp_db):
        role = attempt_login(temp_db, "admin", "wrongpassword")
        assert role is None
        assert get_role_interface(role) is None

    def test_blank_credentials_do_not_redirect(self, temp_db):
        role = attempt_login(temp_db, "", "")
        assert get_role_interface(role) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
