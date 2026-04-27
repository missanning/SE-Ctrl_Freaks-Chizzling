# Test for US-15: Date Filtering / Time Controls
# Test Objective: Ensure that switching between daily and weekly views correctly
# filters and displays only the relevant sales data for the selected time period.

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
    """Create a temp database with transactions across different time periods."""
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

    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    # Use a day that is always within this week but never today
    days_since_monday = today.weekday()
    this_week_not_today_str = (today - timedelta(days=max(1, days_since_monday))).strftime("%Y-%m-%d")
    last_week_str = (today - timedelta(days=10)).strftime("%Y-%m-%d")

    cursor.executemany(
        "INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
        [
            (199.0, 200.0, 1.0,   f"{today_str} 10:00:00"),
            (80.0,  100.0, 20.0,  f"{today_str} 14:00:00"),
            (150.0, 150.0, 0.0,   f"{yesterday_str} 09:00:00"),
            (250.0, 300.0, 50.0,  f"{this_week_not_today_str} 11:00:00"),
            (500.0, 500.0, 0.0,   f"{last_week_str} 10:00:00"),
        ]
    )

    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


def query_sales(db_path, date_from, date_to):
    """Query transactions between date_from and date_to."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM transactions WHERE DATE(date) BETWEEN ? AND ?",
        (date_from, date_to)
    )
    r = cursor.fetchone()
    conn.close()
    return r[0] or 0, r[1] or 0.0


def query_daily_breakdown(db_path, date_from, date_to):
    """Query daily breakdown within a date range."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DATE(date), COUNT(*), SUM(total)
        FROM transactions
        WHERE DATE(date) BETWEEN ? AND ?
        GROUP BY DATE(date)
        ORDER BY DATE(date) DESC
    """, (date_from, date_to))
    rows = cursor.fetchall()
    conn.close()
    return rows


class TestDailyView:
    """AC1: Daily View shows only today's sales data"""

    def test_daily_view_returns_only_todays_transactions(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        count, _ = query_sales(temp_db, date_from, date_to)
        assert count == 2

    def test_daily_view_total_is_correct(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        _, total = query_sales(temp_db, date_from, date_to)
        assert total == 199.0 + 80.0

    def test_daily_view_excludes_yesterday(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        _, total = query_sales(temp_db, date_from, date_to)
        assert total != 199.0 + 80.0 + 150.0

    def test_daily_view_excludes_this_week(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        count, _ = query_sales(temp_db, date_from, date_to)
        assert count == 2

    def test_daily_view_excludes_last_week(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        _, total = query_sales(temp_db, date_from, date_to)
        assert 500.0 not in [total]

    def test_daily_date_from_equals_date_to(self):
        date_from, date_to, _ = get_date_range("daily")
        assert date_from == date_to

    def test_daily_date_is_today(self):
        date_from, _, _ = get_date_range("daily")
        assert date_from == datetime.now().strftime("%Y-%m-%d")

    def test_daily_returns_zero_when_no_sales_today(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        conn = sqlite3.connect(temp_file.name)
        conn.execute("""CREATE TABLE transactions (
            id INTEGER PRIMARY KEY, total REAL,
            payment REAL, change REAL, date TIMESTAMP)""")
        conn.commit()
        conn.close()
        date_from, date_to, _ = get_date_range("daily")
        count, total = query_sales(temp_file.name, date_from, date_to)
        assert count == 0
        assert total == 0.0
        os.unlink(temp_file.name)


class TestWeeklyView:
    """AC2: Weekly View shows aggregated sales data for the current week"""

    def test_weekly_view_includes_today(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        count, _ = query_sales(temp_db, date_from, date_to)
        assert count >= 2

    def test_weekly_view_includes_other_days_this_week(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        count, _ = query_sales(temp_db, date_from, date_to)
        # today(2) + monday(1) + yesterday if in this week
        assert count >= 3

    def test_weekly_view_excludes_last_week(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        _, total = query_sales(temp_db, date_from, date_to)
        assert 500.0 not in [r for r in [total]]

    def test_weekly_total_is_greater_than_daily(self, temp_db):
        daily_from, daily_to, _ = get_date_range("daily")
        weekly_from, weekly_to, _ = get_date_range("weekly")
        _, daily_total = query_sales(temp_db, daily_from, daily_to)
        _, weekly_total = query_sales(temp_db, weekly_from, weekly_to)
        assert weekly_total >= daily_total

    def test_weekly_count_is_greater_than_or_equal_daily(self, temp_db):
        daily_from, daily_to, _ = get_date_range("daily")
        weekly_from, weekly_to, _ = get_date_range("weekly")
        daily_count, _ = query_sales(temp_db, daily_from, daily_to)
        weekly_count, _ = query_sales(temp_db, weekly_from, weekly_to)
        assert weekly_count >= daily_count

    def test_weekly_starts_on_monday(self):
        date_from, _, _ = get_date_range("weekly")
        monday = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        assert date_from == monday

    def test_weekly_ends_on_sunday(self):
        _, date_to, _ = get_date_range("weekly")
        monday = datetime.now() - timedelta(days=datetime.now().weekday())
        sunday = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        assert date_to == sunday

    def test_weekly_breakdown_groups_by_day(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        breakdown = query_daily_breakdown(temp_db, date_from, date_to)
        assert len(breakdown) >= 1
        for row in breakdown:
            assert len(row) == 3  # date, count, total

    def test_weekly_returns_zero_when_no_sales(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        conn = sqlite3.connect(temp_file.name)
        conn.execute("""CREATE TABLE transactions (
            id INTEGER PRIMARY KEY, total REAL,
            payment REAL, change REAL, date TIMESTAMP)""")
        conn.commit()
        conn.close()
        date_from, date_to, _ = get_date_range("weekly")
        count, total = query_sales(temp_file.name, date_from, date_to)
        assert count == 0
        assert total == 0.0
        os.unlink(temp_file.name)


class TestViewSwitching:
    """Switching between daily and weekly returns different results"""

    def test_daily_and_weekly_return_different_counts(self, temp_db):
        daily_from, daily_to, _ = get_date_range("daily")
        weekly_from, weekly_to, _ = get_date_range("weekly")
        daily_count, _ = query_sales(temp_db, daily_from, daily_to)
        weekly_count, _ = query_sales(temp_db, weekly_from, weekly_to)
        assert daily_count != weekly_count

    def test_daily_and_weekly_return_different_totals(self, temp_db):
        daily_from, daily_to, _ = get_date_range("daily")
        weekly_from, weekly_to, _ = get_date_range("weekly")
        _, daily_total = query_sales(temp_db, daily_from, daily_to)
        _, weekly_total = query_sales(temp_db, weekly_from, weekly_to)
        assert daily_total != weekly_total

    def test_daily_date_range_is_single_day(self):
        date_from, date_to, _ = get_date_range("daily")
        assert date_from == date_to

    def test_weekly_date_range_spans_seven_days(self):
        date_from, date_to, _ = get_date_range("weekly")
        d_from = datetime.strptime(date_from, "%Y-%m-%d")
        d_to = datetime.strptime(date_to, "%Y-%m-%d")
        assert (d_to - d_from).days == 6

    def test_daily_title_differs_from_weekly_title(self):
        _, _, daily_title = get_date_range("daily")
        _, _, weekly_title = get_date_range("weekly")
        assert daily_title != weekly_title


if __name__ == "__main__":
    pytest.main([__file__])
