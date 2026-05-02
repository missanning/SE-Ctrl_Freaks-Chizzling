# Test for US-25: Account Management


import pytest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

VALID_ROLES = ["admin", "cashier", "inventory_staff"]

ROLE_INTERFACE = {
    "cashier":         "pos",
    "admin":           "dashboard",
    "inventory_staff": "inventory",
}


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_db():
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


# ── DB helpers (mirror UserManagement logic) ──────────────────────────────────

def get_all_users(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_user_by_username(db_path, username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, role FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_user_by_id(db_path, user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, role FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def add_user(db_path, username, password, role):
    """Returns True on success, False if duplicate, 'invalid' if fields missing/invalid."""
    if not username or not username.strip():
        return "invalid"
    if not password or not password.strip():
        return "invalid"
    if not role or role not in VALID_ROLES:
        return "invalid"
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username.strip(), password.strip(), role)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # duplicate username


def update_user(db_path, user_id, username=None, password=None, role=None):
    """Returns True on success, 'invalid' if required fields missing/invalid."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, role FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    cur_username, cur_password, cur_role = result
    new_username = username.strip() if username and username.strip() else cur_username
    new_role     = role if role and role in VALID_ROLES else cur_role
    new_password = password.strip() if password and password.strip() else cur_password

    if not new_username or not new_role:
        conn.close()
        return "invalid"

    cursor.execute(
        "UPDATE users SET username=?, password=?, role=? WHERE id=?",
        (new_username, new_password, new_role, user_id)
    )
    conn.commit()
    conn.close()
    return True


def delete_user(db_path, user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return True


def login(db_path, username, password):
    if not username or not password:
        return None
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role FROM users WHERE username=? AND password=?",
        (username, password)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


# ── AC1: Admin can view all user accounts ─────────────────────────────────────

class TestViewUserAccounts:
    """AC1: Admin can see a list of all existing user accounts."""

    def test_all_users_are_returned(self, temp_db):
        users = get_all_users(temp_db)
        assert len(users) == 3

    def test_user_list_contains_admin(self, temp_db):
        users = get_all_users(temp_db)
        usernames = [u[1] for u in users]
        assert "admin" in usernames

    def test_user_list_contains_cashier(self, temp_db):
        users = get_all_users(temp_db)
        usernames = [u[1] for u in users]
        assert "cashier" in usernames

    def test_user_list_contains_inventory_staff(self, temp_db):
        users = get_all_users(temp_db)
        usernames = [u[1] for u in users]
        assert "inventory_staff" in usernames

    def test_each_user_has_id(self, temp_db):
        users = get_all_users(temp_db)
        for u in users:
            assert u[0] is not None and isinstance(u[0], int)

    def test_each_user_has_username(self, temp_db):
        users = get_all_users(temp_db)
        for u in users:
            assert isinstance(u[1], str) and len(u[1]) > 0

    def test_each_user_has_role(self, temp_db):
        users = get_all_users(temp_db)
        for u in users:
            assert u[2] in VALID_ROLES

    def test_user_list_is_not_empty(self, temp_db):
        users = get_all_users(temp_db)
        assert len(users) > 0

    def test_user_list_returns_list(self, temp_db):
        users = get_all_users(temp_db)
        assert isinstance(users, list)


# ── AC2: Admin can create a new user account ──────────────────────────────────

class TestCreateUserAccount:
    """AC2: Admin can fill required fields to create a new user account."""

    def test_add_user_returns_true(self, temp_db):
        assert add_user(temp_db, "newuser", "pass123", "cashier") is True

    def test_added_user_appears_in_list(self, temp_db):
        add_user(temp_db, "newuser", "pass123", "cashier")
        users = get_all_users(temp_db)
        usernames = [u[1] for u in users]
        assert "newuser" in usernames

    def test_added_user_has_correct_role(self, temp_db):
        add_user(temp_db, "newuser", "pass123", "cashier")
        user = get_user_by_username(temp_db, "newuser")
        assert user[3] == "cashier"

    def test_user_count_increases_after_add(self, temp_db):
        before = len(get_all_users(temp_db))
        add_user(temp_db, "newuser", "pass123", "cashier")
        after = len(get_all_users(temp_db))
        assert after == before + 1

    def test_add_all_valid_roles(self, temp_db):
        for i, role in enumerate(VALID_ROLES):
            result = add_user(temp_db, f"testuser_{i}", "pass", role)
            assert result is True

    def test_duplicate_username_returns_false(self, temp_db):
        result = add_user(temp_db, "admin", "newpass", "cashier")
        assert result is False

    def test_duplicate_does_not_increase_count(self, temp_db):
        before = len(get_all_users(temp_db))
        add_user(temp_db, "admin", "newpass", "cashier")
        after = len(get_all_users(temp_db))
        assert after == before

    def test_new_user_can_login(self, temp_db):
        add_user(temp_db, "newuser", "pass123", "cashier")
        role = login(temp_db, "newuser", "pass123")
        assert role == "cashier"


# ── AC3: Admin can modify existing user details ───────────────────────────────

class TestModifyUserAccount:
    """AC3: Admin can modify username, password, or role and changes are reflected."""

    def test_update_user_returns_true(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        assert update_user(temp_db, user[0], role="admin") is True

    def test_updated_role_is_reflected(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        update_user(temp_db, user[0], role="admin")
        updated = get_user_by_id(temp_db, user[0])
        assert updated[3] == "admin"

    def test_updated_username_is_reflected(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        update_user(temp_db, user[0], username="cashier_updated")
        updated = get_user_by_id(temp_db, user[0])
        assert updated[1] == "cashier_updated"

    def test_updated_password_is_reflected(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        update_user(temp_db, user[0], password="newpass")
        role = login(temp_db, "cashier", "newpass")
        assert role == "cashier"

    def test_unmodified_fields_remain_unchanged(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        original_username = user[1]
        update_user(temp_db, user[0], role="admin")
        updated = get_user_by_id(temp_db, user[0])
        assert updated[1] == original_username

    def test_update_nonexistent_user_returns_false(self, temp_db):
        result = update_user(temp_db, 9999, username="ghost")
        assert result is False

    def test_user_count_unchanged_after_update(self, temp_db):
        before = len(get_all_users(temp_db))
        user = get_user_by_username(temp_db, "cashier")
        update_user(temp_db, user[0], role="admin")
        after = len(get_all_users(temp_db))
        assert before == after

    def test_updated_user_can_login_with_new_password(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        update_user(temp_db, user[0], password="newpass999")
        role = login(temp_db, "cashier", "newpass999")
        assert role is not None

    def test_old_password_invalid_after_update(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        update_user(temp_db, user[0], password="newpass999")
        role = login(temp_db, "cashier", "1234")
        assert role is None


# ── AC4: Validation prevents invalid input ────────────────────────────────────

class TestValidation:
    """AC4: Empty or invalid fields show error and do not save changes."""

    def test_blank_username_returns_invalid(self, temp_db):
        result = add_user(temp_db, "", "pass", "cashier")
        assert result == "invalid"

    def test_blank_password_returns_invalid(self, temp_db):
        result = add_user(temp_db, "newuser", "", "cashier")
        assert result == "invalid"

    def test_invalid_role_returns_invalid(self, temp_db):
        result = add_user(temp_db, "newuser", "pass", "superadmin")
        assert result == "invalid"

    def test_whitespace_username_returns_invalid(self, temp_db):
        result = add_user(temp_db, "   ", "pass", "cashier")
        assert result == "invalid"

    def test_whitespace_password_returns_invalid(self, temp_db):
        result = add_user(temp_db, "newuser", "   ", "cashier")
        assert result == "invalid"

    def test_invalid_input_does_not_save(self, temp_db):
        before = len(get_all_users(temp_db))
        add_user(temp_db, "", "pass", "cashier")
        after = len(get_all_users(temp_db))
        assert before == after

    def test_none_username_returns_invalid(self, temp_db):
        result = add_user(temp_db, None, "pass", "cashier")
        assert result == "invalid"

    def test_none_password_returns_invalid(self, temp_db):
        result = add_user(temp_db, "newuser", None, "cashier")
        assert result == "invalid"

    def test_valid_roles_are_accepted(self, temp_db):
        for i, role in enumerate(VALID_ROLES):
            result = add_user(temp_db, f"valid_user_{i}", "pass", role)
            assert result is True


# ── AC5: Admin can delete a user account ──────────────────────────────────────

class TestDeleteUserAccount:
    """AC5: Deleted accounts are removed and user can no longer log in."""

    def test_delete_user_returns_true(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        assert delete_user(temp_db, user[0]) is True

    def test_deleted_user_not_in_list(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        delete_user(temp_db, user[0])
        users = get_all_users(temp_db)
        usernames = [u[1] for u in users]
        assert "cashier" not in usernames

    def test_user_count_decreases_after_delete(self, temp_db):
        before = len(get_all_users(temp_db))
        user = get_user_by_username(temp_db, "cashier")
        delete_user(temp_db, user[0])
        after = len(get_all_users(temp_db))
        assert after == before - 1

    def test_deleted_user_cannot_login(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        delete_user(temp_db, user[0])
        role = login(temp_db, "cashier", "1234")
        assert role is None

    def test_delete_nonexistent_user_returns_false(self, temp_db):
        assert delete_user(temp_db, 9999) is False

    def test_other_users_unaffected_after_delete(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        delete_user(temp_db, user[0])
        users = get_all_users(temp_db)
        usernames = [u[1] for u in users]
        assert "admin" in usernames
        assert "inventory_staff" in usernames

    def test_deleted_user_cannot_be_fetched_by_id(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        uid = user[0]
        delete_user(temp_db, uid)
        assert get_user_by_id(temp_db, uid) is None

    def test_deleted_user_can_be_re_added(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        delete_user(temp_db, user[0])
        result = add_user(temp_db, "cashier", "newpass", "cashier")
        assert result is True


# ── AC6: Role-based access is enforced ───────────────────────────────────────

class TestRoleBasedAccess:
    """AC6: Users can only access features permitted for their role."""

    def test_admin_role_maps_to_dashboard(self, temp_db):
        role = login(temp_db, "admin", "1234")
        assert ROLE_INTERFACE.get(role) == "dashboard"

    def test_cashier_role_maps_to_pos(self, temp_db):
        role = login(temp_db, "cashier", "1234")
        assert ROLE_INTERFACE.get(role) == "pos"

    def test_inventory_staff_role_maps_to_inventory(self, temp_db):
        role = login(temp_db, "inventory_staff", "1234")
        assert ROLE_INTERFACE.get(role) == "inventory"

    def test_all_roles_have_defined_interface(self):
        for role in VALID_ROLES:
            assert role in ROLE_INTERFACE

    def test_admin_cannot_access_pos_interface(self, temp_db):
        role = login(temp_db, "admin", "1234")
        assert ROLE_INTERFACE.get(role) != "pos"

    def test_cashier_cannot_access_dashboard(self, temp_db):
        role = login(temp_db, "cashier", "1234")
        assert ROLE_INTERFACE.get(role) != "dashboard"

    def test_inventory_staff_cannot_access_pos(self, temp_db):
        role = login(temp_db, "inventory_staff", "1234")
        assert ROLE_INTERFACE.get(role) != "pos"

    def test_role_change_updates_access(self, temp_db):
        user = get_user_by_username(temp_db, "cashier")
        update_user(temp_db, user[0], role="admin")
        role = login(temp_db, "cashier", "1234")
        assert ROLE_INTERFACE.get(role) == "dashboard"

    def test_invalid_login_has_no_interface(self, temp_db):
        role = login(temp_db, "admin", "wrongpass")
        assert ROLE_INTERFACE.get(role) is None

    def test_new_user_role_determines_interface(self, temp_db):
        add_user(temp_db, "newcashier", "pass", "cashier")
        role = login(temp_db, "newcashier", "pass")
        assert ROLE_INTERFACE.get(role) == "pos"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
