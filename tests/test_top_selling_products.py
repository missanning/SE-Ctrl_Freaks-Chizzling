# Test for US-18: Top-Selling Products


import pytest
import sys
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dashboard_db import get_date_range


# ── Fixture ────────────────────────────────────────────────────────────────────

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
            ("Sizzling Sisig",    199.0, "meals"),
            ("Nachos",             80.0, "snacks"),
            ("Chocolate Milk Tea", 39.0, "drinks"),
            ("Red Horse 1 Litro", 150.0, "alcohol"),
            ("Fries - Cheese",     50.0, "snacks"),
            ("Gin Bilog",          85.0, "alcohol"),
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
            (1782.0, 1800.0, 18.0, f"{today} 10:00:00"),
            (510.0,  510.0,   0.0, f"{this_week_not_today} 09:00:00"),
            (800.0,  800.0,   0.0, f"{last_week} 10:00:00"),
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
            # This week (not today): Gin Bilog x6
            (2, 6, 6, 510.0),
            # Last week: Nachos x10
            (3, 2, 10, 800.0),
        ]
    )

    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def empty_db():
    """Create a temp database with tables but no sales data."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, category TEXT)""")
    cursor.execute("""CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, total REAL,
        payment REAL, change REAL, date TIMESTAMP)""")
    cursor.execute("""CREATE TABLE transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_id INTEGER,
        product_id INTEGER, quantity INTEGER, subtotal REAL)""")
    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


# ── Query helper (mirrors update_top_products DB query) ────────────────────────

def get_top_products(db_path, date_from, date_to, limit=5):
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
        LIMIT ?
    """, (date_from, date_to, limit))
    results = cursor.fetchall()
    conn.close()
    return results


# ── AC1: Summary table is displayed with correct columns ───────────────────────

class TestTopProductsSummaryTable:
    """AC1: System displays Top Products Summary table with name, quantity, revenue."""

    def test_table_returns_results_when_sales_exist(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert len(results) > 0

    def test_table_has_product_name_column(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        for r in results:
            assert isinstance(r[0], str)
            assert len(r[0]) > 0

    def test_table_has_quantity_column(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        for r in results:
            assert isinstance(r[1], int)
            assert r[1] > 0

    def test_table_has_revenue_column(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        for r in results:
            assert isinstance(r[2], float)
            assert r[2] > 0

    def test_table_returns_empty_when_no_sales(self, empty_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(empty_db, date_from, date_to)
        assert results == []

    def test_table_limited_to_top_5(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert len(results) <= 5

    def test_table_returns_exactly_5_when_5_products_sold(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert len(results) == 5

    def test_table_result_is_list(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert isinstance(results, list)

    def test_table_each_row_has_three_columns(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        for r in results:
            assert len(r) == 3


# ── AC2: Table updates based on selected time period ──────────────────────────

class TestTopProductsViewPeriod:
    """AC2: Product list updates when owner selects Daily or Weekly view."""

    def test_daily_view_returns_todays_products(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        names = [r[0] for r in results]
        assert "Sizzling Sisig" in names

    def test_weekly_view_returns_this_weeks_products(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_top_products(temp_db, date_from, date_to)
        names = [r[0] for r in results]
        assert "Gin Bilog" in names

    def test_daily_and_weekly_return_different_results(self, temp_db):
        daily_from, daily_to, _ = get_date_range("daily")
        weekly_from, weekly_to, _ = get_date_range("weekly")
        daily_results = get_top_products(temp_db, daily_from, daily_to)
        weekly_results = get_top_products(temp_db, weekly_from, weekly_to)
        assert daily_results != weekly_results

    def test_daily_excludes_last_week_data(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        # Nachos x10 was last week — should not affect today's ranking
        assert results[0][0] == "Sizzling Sisig"

    def test_weekly_excludes_last_week_data(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_top_products(temp_db, date_from, date_to)
        # Nachos x10 from last week should not appear
        qty_dict = {r[0]: r[1] for r in results}
        if "Nachos" in qty_dict:
            assert qty_dict["Nachos"] == 4  # only today's 4, not last week's 10

    def test_daily_date_range_is_today_only(self):
        date_from, date_to, _ = get_date_range("daily")
        assert date_from == date_to == datetime.now().strftime("%Y-%m-%d")

    def test_weekly_date_range_spans_seven_days(self):
        date_from, date_to, _ = get_date_range("weekly")
        d_from = datetime.strptime(date_from, "%Y-%m-%d")
        d_to   = datetime.strptime(date_to,   "%Y-%m-%d")
        assert (d_to - d_from).days == 6

    def test_daily_title_reflects_period(self):
        _, _, title = get_date_range("daily")
        assert "Today" in title

    def test_weekly_title_reflects_period(self):
        _, _, title = get_date_range("weekly")
        assert "This Week" in title

    def test_empty_result_for_out_of_range_period(self, temp_db):
        results = get_top_products(temp_db, "2000-01-01", "2000-01-31")
        assert results == []


# ── AC3: Quantity and revenue values are accurate ─────────────────────────────

class TestTopProductsAccurateValues:
    """AC3: Products listed with correct quantity and revenue values."""

    def test_top_product_daily_is_sizzling_sisig(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert results[0][0] == "Sizzling Sisig"

    def test_top_product_daily_quantity_is_correct(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert results[0][1] == 5

    def test_top_product_daily_revenue_is_correct(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert results[0][2] == 995.0

    def test_second_product_daily_is_nachos(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert results[1][0] == "Nachos"
        assert results[1][1] == 4
        assert results[1][2] == 320.0

    def test_products_ranked_by_quantity_descending(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        quantities = [r[1] for r in results]
        assert quantities == sorted(quantities, reverse=True)

    def test_weekly_top_product_is_gin_bilog(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_top_products(temp_db, date_from, date_to)
        assert results[0][0] == "Gin Bilog"
        assert results[0][1] == 6

    def test_revenue_values_are_positive(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert all(r[2] > 0 for r in results)

    def test_quantity_values_are_positive_integers(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert all(isinstance(r[1], int) and r[1] > 0 for r in results)

    def test_first_product_has_highest_quantity(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert results[0][1] >= results[-1][1]

    def test_weekly_includes_today_and_this_week(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = get_top_products(temp_db, date_from, date_to)
        names = [r[0] for r in results]
        assert "Sizzling Sisig" in names
        assert "Gin Bilog" in names


# ── AC4: Interactive chart button is available ────────────────────────────────

class TestInteractiveChartAvailability:
    """AC4: View Interactive Chart button is available when data exists."""

    def test_chart_data_has_products(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        products = [r[0] for r in results]
        assert len(products) > 0

    def test_chart_data_has_quantities(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        quantities = [r[1] for r in results]
        assert all(q > 0 for q in quantities)

    def test_chart_data_has_sales(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        sales = [r[2] for r in results]
        assert all(s > 0 for s in sales)

    def test_chart_not_available_when_no_data(self, empty_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(empty_db, date_from, date_to)
        assert len(results) == 0

    def test_chart_data_matches_summary_table(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        # Chart and table use same data source
        products  = [r[0] for r in results]
        quantities = [r[1] for r in results]
        sales     = [r[2] for r in results]
        assert len(products) == len(quantities) == len(sales)

    def test_chart_data_limited_to_top_5(self, temp_db):
        date_from, date_to, _ = get_date_range("daily")
        results = get_top_products(temp_db, date_from, date_to)
        assert len(results) <= 5

    def test_chart_period_title_is_correct_for_daily(self):
        _, _, title = get_date_range("daily")
        assert "Today" in title

    def test_chart_period_title_is_correct_for_weekly(self):
        _, _, title = get_date_range("weekly")
        assert "This Week" in title


# ── AC5: Sales progression chart is available ────────────────────────────────

class TestSalesProgressionChart:
    """AC5: Sales Progression Chart is available based on selected view."""

    def _get_progression_data(self, db_path, period):
        """Simulate open_sales_time_series() data query."""
        date_from, date_to, _ = get_date_range(period)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DATE(t.date), p.name, SUM(ti.quantity), SUM(ti.subtotal)
            FROM transaction_items ti
            JOIN products p ON ti.product_id = p.id
            JOIN transactions t ON ti.transaction_id = t.id
            WHERE DATE(t.date) BETWEEN ? AND ?
            GROUP BY DATE(t.date), p.id, p.name
            ORDER BY DATE(t.date) ASC
        """, (date_from, date_to))
        results = cursor.fetchall()
        conn.close()
        return results

    def test_progression_data_exists_for_daily(self, temp_db):
        results = self._get_progression_data(temp_db, "daily")
        assert len(results) > 0

    def test_progression_data_exists_for_weekly(self, temp_db):
        results = self._get_progression_data(temp_db, "weekly")
        assert len(results) > 0

    def test_progression_data_has_date_column(self, temp_db):
        results = self._get_progression_data(temp_db, "daily")
        for r in results:
            assert isinstance(r[0], str)
            datetime.strptime(r[0], "%Y-%m-%d")  # valid date format

    def test_progression_data_has_product_name(self, temp_db):
        results = self._get_progression_data(temp_db, "daily")
        for r in results:
            assert isinstance(r[1], str) and len(r[1]) > 0

    def test_progression_data_has_quantity(self, temp_db):
        results = self._get_progression_data(temp_db, "daily")
        for r in results:
            assert r[2] > 0

    def test_progression_data_has_revenue(self, temp_db):
        results = self._get_progression_data(temp_db, "daily")
        for r in results:
            assert r[3] > 0

    def test_progression_weekly_has_more_data_than_daily(self, temp_db):
        daily_results  = self._get_progression_data(temp_db, "daily")
        weekly_results = self._get_progression_data(temp_db, "weekly")
        assert len(weekly_results) >= len(daily_results)

    def test_progression_empty_when_no_sales(self, empty_db):
        results = self._get_progression_data(empty_db, "daily")
        assert results == []

    def test_progression_daily_dates_are_today(self, temp_db):
        results = self._get_progression_data(temp_db, "daily")
        today = datetime.now().strftime("%Y-%m-%d")
        dates = [r[0] for r in results]
        assert all(d == today for d in dates)

    def test_progression_weekly_dates_within_range(self, temp_db):
        date_from, date_to, _ = get_date_range("weekly")
        results = self._get_progression_data(temp_db, "weekly")
        for r in results:
            assert date_from <= r[0] <= date_to


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
