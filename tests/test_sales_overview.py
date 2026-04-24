# Test for US-04: Sales Overview for Admin

import pytest
import sys
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dashboard_db import get_date_range


@pytest.fixture
def temp_db():
    """Create a temp database with transactions for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL,
        payment REAL,
        change REAL,
        date TIMESTAMP
    )
    """)

    today = datetime.now().strftime("%Y-%m-%d")
    monday = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    last_week = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    transactions = [
        # Today's transactions
        (199.0, 200.0, 1.0,  f"{today} 10:00:00"),
        (80.0,  100.0, 20.0, f"{today} 11:00:00"),
        (39.0,  40.0,  1.0,  f"{today} 12:00:00"),
        # This week (not today)
        (150.0, 150.0, 0.0,  f"{monday} 09:00:00"),
        (250.0, 300.0, 50.0, f"{monday} 14:00:00"),
        # Last week (outside current week)
        (500.0, 500.0, 0.0,  f"{last_week} 10:00:00"),
    ]

    cursor.executemany(
        "INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
        transactions
    )
    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


def get_daily_sales(db_path):
    """Simulate show_daily_sales() DB query."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*), SUM(total) FROM transactions WHERE date LIKE ?",
        (today + '%',)
    )
    r = cursor.fetchone()
    conn.close()
    count = r[0] or 0
    total = r[1] or 0.0
    avg = total / count if count else 0.0
    return count, total, avg


def get_weekly_sales(db_path):
    """Simulate show_weekly_sales() DB query."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    date_from = monday.strftime("%Y-%m-%d")
    date_to = sunday.strftime("%Y-%m-%d")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*), SUM(total) FROM transactions WHERE DATE(date) BETWEEN ? AND ?",
        (date_from, date_to)
    )
    r = cursor.fetchone()

    cursor.execute("""
        SELECT DATE(date), COUNT(*), SUM(total) FROM transactions
        WHERE DATE(date) BETWEEN ? AND ?
        GROUP BY DATE(date) ORDER BY DATE(date) DESC
    """, (date_from, date_to))
    daily_breakdown = cursor.fetchall()
    conn.close()

    count = r[0] or 0
    total = r[1] or 0.0
    days_elapsed = (today - monday).days + 1
    avg_daily = total / days_elapsed if days_elapsed else 0.0
    return count, total, avg_daily, daily_breakdown


class TestDailySales:
    """AC1: Total daily sales are displayed when dashboard is opened"""

    def test_daily_transaction_count(self, temp_db):
        count, _, _ = get_daily_sales(temp_db)
        assert count == 3

    def test_daily_total_sales(self, temp_db):
        _, total, _ = get_daily_sales(temp_db)
        assert total == 199.0 + 80.0 + 39.0

    def test_daily_average_transaction(self, temp_db):
        count, total, avg = get_daily_sales(temp_db)
        assert avg == total / count

    def test_daily_total_is_float(self, temp_db):
        _, total, _ = get_daily_sales(temp_db)
        assert isinstance(total, float)

    def test_daily_count_is_int(self, temp_db):
        count, _, _ = get_daily_sales(temp_db)
        assert isinstance(count, int)

    def test_daily_sales_excludes_other_days(self, temp_db):
        count, _, _ = get_daily_sales(temp_db)
        # Only 3 transactions today, not 6 total
        assert count == 3

    def test_daily_returns_zero_on_empty_db(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        conn = sqlite3.connect(temp_file.name)
        conn.execute("""CREATE TABLE transactions (
            id INTEGER PRIMARY KEY, total REAL, payment REAL, change REAL, date TIMESTAMP)""")
        conn.commit()
        conn.close()
        count, total, avg = get_daily_sales(temp_file.name)
        assert count == 0
        assert total == 0.0
        assert avg == 0.0
        os.unlink(temp_file.name)

    def test_daily_avg_is_zero_when_no_transactions(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        conn = sqlite3.connect(temp_file.name)
        conn.execute("""CREATE TABLE transactions (
            id INTEGER PRIMARY KEY, total REAL, payment REAL, change REAL, date TIMESTAMP)""")
        conn.commit()
        conn.close()
        _, _, avg = get_daily_sales(temp_file.name)
        assert avg == 0.0
        os.unlink(temp_file.name)


class TestWeeklySales:
    """AC2: Total weekly sales are displayed when weekly summary is available"""

    def test_weekly_transaction_count(self, temp_db):
        count, _, _, _ = get_weekly_sales(temp_db)
        # 3 today + 2 on monday = 5 (last_week is excluded)
        assert count == 5

    def test_weekly_total_sales(self, temp_db):
        _, total, _, _ = get_weekly_sales(temp_db)
        assert total == 199.0 + 80.0 + 39.0 + 150.0 + 250.0

    def test_weekly_excludes_last_week(self, temp_db):
        _, total, _, _ = get_weekly_sales(temp_db)
        # 500.0 from last week should not be included
        assert total != 199.0 + 80.0 + 39.0 + 150.0 + 250.0 + 500.0

    def test_weekly_daily_average_is_positive(self, temp_db):
        _, _, avg_daily, _ = get_weekly_sales(temp_db)
        assert avg_daily > 0

    def test_weekly_daily_breakdown_is_not_empty(self, temp_db):
        _, _, _, breakdown = get_weekly_sales(temp_db)
        assert len(breakdown) > 0

    def test_weekly_breakdown_has_correct_columns(self, temp_db):
        _, _, _, breakdown = get_weekly_sales(temp_db)
        # Each row: (date, count, total)
        for row in breakdown:
            assert len(row) == 3

    def test_weekly_breakdown_totals_match_weekly_total(self, temp_db):
        _, total, _, breakdown = get_weekly_sales(temp_db)
        breakdown_total = sum(row[2] for row in breakdown)
        assert round(breakdown_total, 2) == round(total, 2)

    def test_weekly_returns_zero_on_empty_db(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        conn = sqlite3.connect(temp_file.name)
        conn.execute("""CREATE TABLE transactions (
            id INTEGER PRIMARY KEY, total REAL, payment REAL, change REAL, date TIMESTAMP)""")
        conn.commit()
        conn.close()
        count, total, avg_daily, breakdown = get_weekly_sales(temp_file.name)
        assert count == 0
        assert total == 0.0
        assert breakdown == []
        os.unlink(temp_file.name)


class TestGetDateRange:
    """Test get_date_range() utility used by both daily and weekly views"""

    def test_daily_date_range_returns_today(self):
        date_from, date_to, title = get_date_range("daily")
        today = datetime.now().strftime("%Y-%m-%d")
        assert date_from == today
        assert date_to == today

    def test_daily_title_contains_today(self):
        _, _, title = get_date_range("daily")
        assert "Today" in title

    def test_weekly_date_range_starts_on_monday(self):
        date_from, _, _ = get_date_range("weekly")
        monday = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        assert date_from == monday

    def test_weekly_date_range_ends_on_sunday(self):
        _, date_to, _ = get_date_range("weekly")
        monday = datetime.now() - timedelta(days=datetime.now().weekday())
        sunday = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        assert date_to == sunday

    def test_weekly_title_contains_this_week(self):
        _, _, title = get_date_range("weekly")
        assert "This Week" in title

    def test_monthly_date_range_starts_on_first(self):
        date_from, _, _ = get_date_range("monthly")
        first = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        assert date_from == first

    def test_monthly_title_contains_this_month(self):
        _, _, title = get_date_range("monthly")
        assert "This Month" in title

    def test_date_range_returns_tuple_of_three(self):
        result = get_date_range("daily")
        assert len(result) == 3


if __name__ == "__main__":
    pytest.main([__file__])
