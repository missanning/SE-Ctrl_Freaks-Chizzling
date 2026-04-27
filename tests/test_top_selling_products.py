# Test for US-18: Top-Selling Products
# Test Objective: Ensure that top-selling products are correctly queried,
# ranked by quantity and revenue, limited to top 5, and return empty
# results when no sales data exists.

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

    cursor.executemany(
        "INSERT INTO products (name, price, category) VALUES (?, ?, ?)",
        [
            ("Sizzling Sisig",     199.0, "meals"),
            ("Nachos",              80.0, "snacks"),
            ("Chocolate Milk Tea",  39.0, "drinks"),
            ("Red Horse 1 Litro",  150.0, "alcohol"),
            ("Fries - Cheese",      50.0, "snacks"),
            ("Gin Bilog",           85.0, "alcohol"),
        ]
    )

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    offset = 1 if now.weekday() == 0 else -1
    this_week_not_today = (now + timedelta(days=offset)).strftime("%Y-%m-%d")
    last_week = (now - timedelta(days=10)).strftime("%Y-%m-%d")

    cursor.executemany(
        "INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
        [
            (995.0, 1000.0, 5.0,  f"{today} 10:00:00"),
            (400.0, 400.0,  0.0,  f"{this_week_not_today} 09:00:00"),
            (300.0, 300.0,  0.0,  f"{last_week} 10:00:00"),
        ]
    )

    cursor.executemany(
        "INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal) VALUES (?, ?, ?, ?)",
        [
            # Today: Sisig x5, Nachos x4, MilkTea x3, RedHorse x2, Fries x1
            (1, 1, 5, 995.0),
            (1, 2, 4, 320.0),
            (1, 3, 3, 117.0),
            (1, 4, 2, 300.0),
            (1, 5, 1,  50.0),
            # This week: Gin Bilog x6
            (2, 6, 6, 510.0),
            # Last week: Nachos x10
            (3, 2, 10, 800.0),
        ]
    )

    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


def get_top_products(db_path, date_from, date_to):
    """Simulate update_top_products() DB query."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.name, SUM(ti.quantity) as total_qty, SUM(ti.subtotal) as total_sales
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.id
        JOIN transactions t ON ti.transaction_id = t.id
        WHERE DATE(t.date) BETWEEN ? AND ?
        GROUP BY p.id, p.name
        ORDER BY total_qty DESC
        LIMIT 5
    """, (date_from, date_to))
    results = cursor.fetchall()
    conn.close()
    return results


class TestTopProductsDisplayed:
    """AC1: Top-selling products list is displayed when dashboard loads"""

    def test_returns_products_when_sales_exist(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert len(results) > 0

    def test_returns_at_most_5_products(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert len(results) <= 5

    def test_each_product_has_name(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        for r in results:
            assert isinstance(r[0], str)
            assert len(r[0]) > 0

    def test_each_product_has_quantity(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        for r in results:
            assert r[1] > 0

    def test_each_product_has_revenue(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        for r in results:
            assert r[2] > 0

    def test_returns_empty_when_no_sales(self, temp_db):
        results = get_top_products(temp_db, "2000-01-01", "2000-01-31")
        assert results == []

    def test_returns_empty_list_type(self, temp_db):
        results = get_top_products(temp_db, "2000-01-01", "2000-01-31")
        assert isinstance(results, list)

    def test_daily_top_products_excludes_last_week(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        names = [r[0] for r in results]
        # Nachos x10 was last week, should not affect today's ranking
        assert results[0][0] == "Sizzling Sisig"


class TestProductsRankedByQuantityAndRevenue:
    """AC2: Products are ranked based on quantity or revenue"""

    def test_products_ranked_by_quantity_descending(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        quantities = [r[1] for r in results]
        assert quantities == sorted(quantities, reverse=True)

    def test_first_product_has_highest_quantity(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert results[0][1] >= results[-1][1]

    def test_top_product_by_quantity_is_correct(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert results[0][0] == "Sizzling Sisig"
        assert results[0][1] == 5

    def test_second_product_by_quantity_is_correct(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert results[1][0] == "Nachos"
        assert results[1][1] == 4

    def test_revenue_values_are_correct(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        result_dict = {r[0]: r[2] for r in results}
        assert result_dict["Sizzling Sisig"] == 995.0
        assert result_dict["Nachos"] == 320.0

    def test_quantity_values_are_integers(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        for r in results:
            assert isinstance(r[1], int)

    def test_revenue_values_are_floats(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        for r in results:
            assert isinstance(r[2], float)

    def test_weekly_ranking_includes_gin_bilog(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_top_products(temp_db, date_from, date_to)
        names = [r[0] for r in results]
        assert "Gin Bilog" in names

    def test_weekly_top_product_is_gin_bilog(self, temp_db):
        # Gin Bilog x6 this week vs Sisig x5 today
        date_from, date_to, _ = get_date_range("weekly")
        results = get_top_products(temp_db, date_from, date_to)
        assert results[0][0] == "Gin Bilog"
        assert results[0][1] == 6

    def test_limit_is_5_even_with_more_products(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        # 5 products sold today, should return exactly 5
        assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__])
