# Test for US-07: Profitable Products Report
# Test Objective: Ensure that products are correctly ranked by total revenue,
# revenue values and quantities are accurate, and results update per time period.

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
    """Create a temp database with products, transactions, and transaction items."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        price REAL,
        category TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL,
        payment REAL,
        change REAL,
        date TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        subtotal REAL,
        FOREIGN KEY(transaction_id) REFERENCES transactions(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    # Products
    cursor.executemany(
        "INSERT INTO products (name, price, category) VALUES (?, ?, ?)",
        [
            ("Sizzling Sisig",     199.0, "meals"),
            ("Nachos",              80.0, "snacks"),
            ("Chocolate Milk Tea",  39.0, "drinks"),
            ("Red Horse 1 Litro",  150.0, "alcohol"),
        ]
    )

    today = datetime.now().strftime("%Y-%m-%d")
    monday = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    first_of_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    last_month = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")

    # Transactions
    cursor.executemany(
        "INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
        [
            (398.0, 400.0, 2.0,  f"{today} 10:00:00"),       # id=1 today
            (160.0, 200.0, 40.0, f"{monday} 09:00:00"),       # id=2 this week
            (117.0, 120.0, 3.0,  f"{first_of_month} 08:00:00"), # id=3 this month
            (300.0, 300.0, 0.0,  f"{last_month} 10:00:00"),   # id=4 last month
        ]
    )

    # Transaction items
    cursor.executemany(
        "INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal) VALUES (?, ?, ?, ?)",
        [
            # Today: Sisig x2=398, Nachos x1=80 (but in separate transactions for simplicity)
            (1, 1, 2, 398.0),   # Sizzling Sisig x2
            (2, 2, 2, 160.0),   # Nachos x2 (this week)
            (3, 3, 3, 117.0),   # Milk Tea x3 (this month)
            (4, 4, 2, 300.0),   # Red Horse x2 (last month)
        ]
    )

    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


def get_revenue_report(db_path, date_from, date_to):
    """Simulate update_revenue_analysis() DB query."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.name, p.price, SUM(ti.quantity) as total_qty,
               SUM(ti.subtotal) as total_revenue,
               AVG(p.price) as avg_price,
               (SUM(ti.subtotal) / SUM(ti.quantity)) as avg_revenue_per_unit
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.id
        JOIN transactions t ON ti.transaction_id = t.id
        WHERE DATE(t.date) BETWEEN ? AND ?
        GROUP BY p.id, p.name, p.price
        HAVING SUM(ti.quantity) > 0
        ORDER BY total_revenue DESC
    """, (date_from, date_to))
    results = cursor.fetchall()
    conn.close()
    return results


class TestProductsRankedByRevenue:
    """AC1: Products are ranked by total revenue (price x quantity sold)"""

    def test_products_ordered_by_revenue_descending(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_revenue_report(temp_db, date_from, date_to)
        revenues = [r[3] for r in results]
        assert revenues == sorted(revenues, reverse=True)

    def test_highest_revenue_product_is_first(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_revenue_report(temp_db, date_from, date_to)
        assert results[0][3] >= results[-1][3]

    def test_revenue_equals_price_times_quantity(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_revenue_report(temp_db, date_from, date_to)
        for r in results:
            # subtotal should equal price * qty
            expected = r[1] * r[2]
            assert round(r[3], 2) == round(expected, 2)

    def test_returns_only_products_with_sales(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_revenue_report(temp_db, date_from, date_to)
        assert all(r[2] > 0 for r in results)

    def test_empty_result_for_period_with_no_sales(self, temp_db):
        results = get_revenue_report(temp_db, "2000-01-01", "2000-01-31")
        assert results == []

    def test_result_is_list(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_revenue_report(temp_db, date_from, date_to)
        assert isinstance(results, list)


class TestRevenueValuesAndQuantities:
    """AC2: Revenue values and sales quantities are shown accurately"""

    def test_daily_revenue_is_correct(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_revenue_report(temp_db, date_from, date_to)
        # Today: Sizzling Sisig x2 = 398.0
        assert len(results) == 1
        assert results[0][0] == "Sizzling Sisig"
        assert results[0][3] == 398.0

    def test_daily_quantity_is_correct(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_revenue_report(temp_db, date_from, date_to)
        assert results[0][2] == 2

    def test_product_name_is_present(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_revenue_report(temp_db, date_from, date_to)
        assert all(isinstance(r[0], str) and len(r[0]) > 0 for r in results)

    def test_unit_price_is_present(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_revenue_report(temp_db, date_from, date_to)
        assert all(r[1] > 0 for r in results)

    def test_avg_revenue_per_unit_is_correct(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_revenue_report(temp_db, date_from, date_to)
        for r in results:
            expected_avg = r[3] / r[2]
            assert round(r[5], 2) == round(expected_avg, 2)

    def test_total_revenue_calculation(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_revenue_report(temp_db, date_from, date_to)
        total = sum(r[3] for r in results)
        assert total == 398.0 + 160.0

    def test_total_quantity_calculation(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_revenue_report(temp_db, date_from, date_to)
        total_qty = sum(r[2] for r in results)
        assert total_qty == 4  # Sisig x2 + Nachos x2


class TestRevenuePeriodFilter:
    """AC3: Revenue analysis updates correctly per time period"""

    def test_daily_returns_only_todays_data(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_revenue_report(temp_db, date_from, date_to)
        names = [r[0] for r in results]
        assert "Sizzling Sisig" in names
        assert "Nachos" not in names
        assert "Chocolate Milk Tea" not in names

    def test_weekly_returns_this_weeks_data(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_revenue_report(temp_db, date_from, date_to)
        names = [r[0] for r in results]
        assert "Sizzling Sisig" in names
        assert "Nachos" in names

    def test_weekly_excludes_last_month_data(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_revenue_report(temp_db, date_from, date_to)
        names = [r[0] for r in results]
        assert "Red Horse 1 Litro" not in names

    def test_monthly_returns_more_data_than_daily(self, temp_db):
        daily_from, daily_to, _ = get_date_range("daily")
        monthly_from, monthly_to, _ = get_date_range("monthly")
        daily_results = get_revenue_report(temp_db, daily_from, daily_to)
        monthly_results = get_revenue_report(temp_db, monthly_from, monthly_to)
        assert len(monthly_results) >= len(daily_results)

    def test_monthly_excludes_last_month_data(self, temp_db):
        date_from, date_to, _ = get_date_range("monthly")
        results = get_revenue_report(temp_db, date_from, date_to)
        names = [r[0] for r in results]
        assert "Red Horse 1 Litro" not in names

    def test_different_periods_return_different_results(self, temp_db):
        daily_from, daily_to, _ = get_date_range("daily")
        weekly_from, weekly_to, _ = get_date_range("weekly")
        daily_results = get_revenue_report(temp_db, daily_from, daily_to)
        weekly_results = get_revenue_report(temp_db, weekly_from, weekly_to)
        assert daily_results != weekly_results

    def test_period_title_reflects_selected_period(self):
        _, _, daily_title = get_date_range("daily")
        _, _, weekly_title = get_date_range("weekly")
        _, _, monthly_title = get_date_range("monthly")
        assert "Today" in daily_title
        assert "This Week" in weekly_title
        assert "This Month" in monthly_title


if __name__ == "__main__":
    pytest.main([__file__])
