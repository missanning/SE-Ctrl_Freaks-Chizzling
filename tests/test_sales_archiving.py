# Test for US-24: Sales Data Archiving


import pytest
import sys
import os
import sqlite3
import tempfile
import calendar
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── Helpers (mirror sales_archive.py logic) ────────────────────────────────────

def month_range(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return (f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last_day:02d}")


def get_active_transactions(db_path, date_from=None, date_to=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if date_from and date_to:
        cursor.execute(
            "SELECT id, total, payment, change, date FROM transactions WHERE DATE(date) BETWEEN ? AND ?",
            (date_from, date_to)
        )
    else:
        cursor.execute("SELECT id, total, payment, change, date FROM transactions")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_archived_transactions(db_path, date_from=None, date_to=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if date_from and date_to:
        cursor.execute(
            "SELECT id, total, payment, change, date FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?",
            (date_from, date_to)
        )
    else:
        cursor.execute("SELECT id, total, payment, change, date FROM transaction_archive")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_archived_items(db_path, transaction_id=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if transaction_id:
        cursor.execute(
            "SELECT * FROM transaction_items_archive WHERE transaction_id=?",
            (transaction_id,)
        )
    else:
        cursor.execute("SELECT * FROM transaction_items_archive")
    rows = cursor.fetchall()
    conn.close()
    return rows


def archive_by_month(db_path, year, month):
    """Move transactions for a given month from active to archive. Returns count archived."""
    date_from, date_to = month_range(year, month)

    # Prevent archiving current month
    now = datetime.now()
    if year == now.year and month == now.month:
        return -1  # signal: cannot archive current month

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM transactions WHERE DATE(date) BETWEEN ? AND ?",
        (date_from, date_to)
    )
    count = cursor.fetchone()[0]

    if count == 0:
        conn.close()
        return 0

    cursor.execute("""
        INSERT INTO transaction_archive (id, total, payment, change, date)
        SELECT id, total, payment, change, date FROM transactions
        WHERE DATE(date) BETWEEN ? AND ?
    """, (date_from, date_to))
    cursor.execute("""
        INSERT INTO transaction_items_archive (id, transaction_id, product_id, quantity, subtotal)
        SELECT ti.id, ti.transaction_id, ti.product_id, ti.quantity, ti.subtotal
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        WHERE DATE(t.date) BETWEEN ? AND ?
    """, (date_from, date_to))
    cursor.execute("""
        DELETE FROM transaction_items WHERE transaction_id IN
        (SELECT id FROM transactions WHERE DATE(date) BETWEEN ? AND ?)
    """, (date_from, date_to))
    cursor.execute(
        "DELETE FROM transactions WHERE DATE(date) BETWEEN ? AND ?",
        (date_from, date_to)
    )
    conn.commit()
    conn.close()
    return count


def restore_by_month(db_path, year, month):
    """Restore archived transactions for a given month back to active. Returns count restored."""
    date_from, date_to = month_range(year, month)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?",
        (date_from, date_to)
    )
    count = cursor.fetchone()[0]
    if count == 0:
        conn.close()
        return 0

    cursor.execute("""
        INSERT OR IGNORE INTO transactions (id, total, payment, change, date)
        SELECT id, total, payment, change, date FROM transaction_archive
        WHERE DATE(date) BETWEEN ? AND ?
    """, (date_from, date_to))
    cursor.execute("""
        INSERT OR IGNORE INTO transaction_items (id, transaction_id, product_id, quantity, subtotal)
        SELECT id, transaction_id, product_id, quantity, subtotal
        FROM transaction_items_archive
        WHERE transaction_id IN (
            SELECT id FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?
        )
    """, (date_from, date_to))
    cursor.execute("""
        DELETE FROM transaction_items_archive
        WHERE transaction_id IN (
            SELECT id FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?
        )
    """, (date_from, date_to))
    cursor.execute(
        "DELETE FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?",
        (date_from, date_to)
    )
    conn.commit()
    conn.close()
    return count


def delete_archived_month(db_path, year, month):
    """Permanently delete archived transactions for a given month. Returns count deleted."""
    date_from, date_to = month_range(year, month)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?",
        (date_from, date_to)
    )
    count = cursor.fetchone()[0]
    if count == 0:
        conn.close()
        return 0
    cursor.execute("""
        DELETE FROM transaction_items_archive
        WHERE transaction_id IN (
            SELECT id FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?
        )
    """, (date_from, date_to))
    cursor.execute(
        "DELETE FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?",
        (date_from, date_to)
    )
    conn.commit()
    conn.close()
    return count


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Create a temp database with transactions across different months."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL, payment REAL, change REAL, date TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER, product_id INTEGER,
        quantity INTEGER, subtotal REAL
    )
    """)
    cursor.execute("""
    CREATE TABLE transaction_archive (
        id INTEGER PRIMARY KEY,
        total REAL, payment REAL, change REAL, date TIMESTAMP,
        archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE transaction_items_archive (
        id INTEGER PRIMARY KEY,
        transaction_id INTEGER, product_id INTEGER,
        quantity INTEGER, subtotal REAL
    )
    """)

    now = datetime.now()
    # Use 2 months ago to safely avoid current month restriction
    two_months_ago = (now.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)
    old_year  = two_months_ago.year
    old_month = two_months_ago.month
    old_date  = f"{old_year}-{old_month:02d}-15"

    last_month_dt = (now.replace(day=1) - timedelta(days=1))
    last_year  = last_month_dt.year
    last_month = last_month_dt.month
    last_date  = f"{last_year}-{last_month:02d}-10"

    today = now.strftime("%Y-%m-%d")

    cursor.executemany(
        "INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
        [
            (199.0, 200.0, 1.0,  f"{old_date} 10:00:00"),   # id=1 two months ago
            (80.0,  100.0, 20.0, f"{old_date} 11:00:00"),   # id=2 two months ago
            (150.0, 150.0, 0.0,  f"{last_date} 09:00:00"),  # id=3 last month
            (250.0, 300.0, 50.0, f"{today} 10:00:00"),      # id=4 today (current month)
        ]
    )
    cursor.executemany(
        "INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal) VALUES (?, ?, ?, ?)",
        [
            (1, 1, 1, 199.0),
            (2, 2, 1,  80.0),
            (3, 3, 1, 150.0),
            (4, 1, 2, 250.0),
        ]
    )

    conn.commit()
    conn.close()

    # Store date info for use in tests
    temp_file.old_year   = old_year
    temp_file.old_month  = old_month
    temp_file.last_year  = last_year
    temp_file.last_month = last_month

    yield temp_file

    try:
        os.unlink(temp_file.name)
    except PermissionError:
        pass


# ── AC1: Records are moved to archived storage ────────────────────────────────

class TestArchiveSalesData:
    """AC1: Sales records are moved to archive and removed from active transactions."""

    def test_archive_returns_correct_count(self, temp_db):
        count = archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        assert count == 2

    def test_archived_records_removed_from_active(self, temp_db):
        date_from, date_to = month_range(temp_db.old_year, temp_db.old_month)
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        active = get_active_transactions(temp_db.name, date_from, date_to)
        assert active == []

    def test_archived_records_appear_in_archive(self, temp_db):
        date_from, date_to = month_range(temp_db.old_year, temp_db.old_month)
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        archived = get_archived_transactions(temp_db.name, date_from, date_to)
        assert len(archived) == 2

    def test_active_count_decreases_after_archive(self, temp_db):
        before = len(get_active_transactions(temp_db.name))
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        after = len(get_active_transactions(temp_db.name))
        assert after == before - 2

    def test_archive_count_increases_after_archive(self, temp_db):
        before = len(get_archived_transactions(temp_db.name))
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        after = len(get_archived_transactions(temp_db.name))
        assert after == before + 2

    def test_transaction_items_moved_to_archive(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        items = get_archived_items(temp_db.name)
        assert len(items) == 2

    def test_transaction_items_removed_from_active(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transaction_items WHERE transaction_id IN (1, 2)")
        rows = cursor.fetchall()
        conn.close()
        assert rows == []

    def test_current_month_cannot_be_archived(self, temp_db):
        now = datetime.now()
        result = archive_by_month(temp_db.name, now.year, now.month)
        assert result == -1

    def test_current_month_transactions_remain_active(self, temp_db):
        now = datetime.now()
        archive_by_month(temp_db.name, now.year, now.month)
        today = now.strftime("%Y-%m-%d")
        active = get_active_transactions(temp_db.name, today, today)
        assert len(active) == 1

    def test_archive_empty_month_returns_zero(self, temp_db):
        result = archive_by_month(temp_db.name, 2000, 1)
        assert result == 0

    def test_other_months_unaffected_after_archive(self, temp_db):
        date_from, date_to = month_range(temp_db.last_year, temp_db.last_month)
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        last_month_active = get_active_transactions(temp_db.name, date_from, date_to)
        assert len(last_month_active) == 1

    def test_archived_data_retains_correct_totals(self, temp_db):
        date_from, date_to = month_range(temp_db.old_year, temp_db.old_month)
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        archived = get_archived_transactions(temp_db.name, date_from, date_to)
        totals = sorted([r[1] for r in archived])
        assert totals == [80.0, 199.0]

    def test_archive_multiple_months(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        archive_by_month(temp_db.name, temp_db.last_year, temp_db.last_month)
        all_archived = get_archived_transactions(temp_db.name)
        assert len(all_archived) == 3


# ── AC2: Archived data can still be retrieved ─────────────────────────────────

class TestRetrieveArchivedData:
    """AC2: Archived records can be retrieved, viewed, restored, and deleted."""

    def test_archived_records_are_retrievable(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        archived = get_archived_transactions(temp_db.name)
        assert len(archived) > 0

    def test_archived_records_have_correct_fields(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        archived = get_archived_transactions(temp_db.name)
        for r in archived:
            assert len(r) == 5  # id, total, payment, change, date

    def test_retrieve_by_specific_month(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        date_from, date_to = month_range(temp_db.old_year, temp_db.old_month)
        archived = get_archived_transactions(temp_db.name, date_from, date_to)
        assert len(archived) == 2

    def test_retrieve_returns_correct_totals(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        date_from, date_to = month_range(temp_db.old_year, temp_db.old_month)
        archived = get_archived_transactions(temp_db.name, date_from, date_to)
        total = sum(r[1] for r in archived)
        assert total == 199.0 + 80.0

    def test_archived_items_are_retrievable(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        items = get_archived_items(temp_db.name)
        assert len(items) == 2

    def test_restore_returns_correct_count(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        count = restore_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        assert count == 2

    def test_restored_records_appear_in_active(self, temp_db):
        date_from, date_to = month_range(temp_db.old_year, temp_db.old_month)
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        restore_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        active = get_active_transactions(temp_db.name, date_from, date_to)
        assert len(active) == 2

    def test_restored_records_removed_from_archive(self, temp_db):
        date_from, date_to = month_range(temp_db.old_year, temp_db.old_month)
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        restore_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        archived = get_archived_transactions(temp_db.name, date_from, date_to)
        assert archived == []

    def test_restored_items_appear_in_active(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        restore_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transaction_items WHERE transaction_id IN (1, 2)")
        rows = cursor.fetchall()
        conn.close()
        assert len(rows) == 2

    def test_restore_empty_month_returns_zero(self, temp_db):
        result = restore_by_month(temp_db.name, 2000, 1)
        assert result == 0

    def test_delete_archived_month_returns_correct_count(self, temp_db):
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        count = delete_archived_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        assert count == 2

    def test_deleted_archived_records_not_retrievable(self, temp_db):
        date_from, date_to = month_range(temp_db.old_year, temp_db.old_month)
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        delete_archived_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        archived = get_archived_transactions(temp_db.name, date_from, date_to)
        assert archived == []

    def test_deleted_archived_records_not_in_active(self, temp_db):
        date_from, date_to = month_range(temp_db.old_year, temp_db.old_month)
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        delete_archived_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        active = get_active_transactions(temp_db.name, date_from, date_to)
        assert active == []

    def test_delete_empty_archived_month_returns_zero(self, temp_db):
        result = delete_archived_month(temp_db.name, 2000, 1)
        assert result == 0

    def test_archive_then_restore_preserves_data_integrity(self, temp_db):
        date_from, date_to = month_range(temp_db.old_year, temp_db.old_month)
        original = get_active_transactions(temp_db.name, date_from, date_to)
        archive_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        restore_by_month(temp_db.name, temp_db.old_year, temp_db.old_month)
        restored = get_active_transactions(temp_db.name, date_from, date_to)
        orig_totals = sorted([r[1] for r in original])
        rest_totals = sorted([r[1] for r in restored])
        assert orig_totals == rest_totals


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
