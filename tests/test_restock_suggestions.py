# Test for US-06: Restock Suggestions


import pytest
import sys
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── Constants (mirrors ProductManagementSystem.stocks threshold) ───────────────
LOW_STOCK_THRESHOLD = 30


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Create a temp database with products and transaction data."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE products (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        name     TEXT UNIQUE,
        price    REAL,
        stock    INTEGER,
        category TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE transactions (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        total   REAL,
        payment REAL,
        change  REAL,
        date    TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE transaction_items (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER,
        product_id     INTEGER,
        quantity       INTEGER,
        subtotal       REAL
    )
    """)

    # Products with varying stock levels
    cursor.executemany(
        "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
        [
            ("Sizzling Sisig",  199.0,  5,  "meals"),    # low stock
            ("Nachos",           80.0, 10,  "snacks"),   # low stock
            ("Gin Bilog",        85.0, 30,  "alcohol"),  # at threshold
            ("Fries - Cheese",   50.0, 31,  "snacks"),   # just above threshold
            ("Chocolate Milk Tea", 39.0, 100, "drinks"), # sufficient stock
            ("Red Horse 1 Litro", 150.0, 200, "alcohol"),# sufficient stock
        ]
    )

    # Sales data — Sizzling Sisig and Nachos are popular (high quantity sold)
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
        (1000.0, 1000.0, 0.0, f"{today} 10:00:00")
    )
    cursor.executemany(
        "INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal) VALUES (?, ?, ?, ?)",
        [
            (1, 1, 50, 9950.0),  # Sizzling Sisig — most popular
            (1, 2, 40, 3200.0),  # Nachos — second most popular
            (1, 3,  5,  425.0),  # Gin Bilog
            (1, 4,  2,  100.0),  # Fries
        ]
    )

    conn.commit()
    conn.close()

    yield temp_file.name

    try:
        os.unlink(temp_file.name)
    except PermissionError:
        pass


@pytest.fixture
def all_sufficient_db():
    """Database where all products have sufficient stock."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE, price REAL, stock INTEGER, category TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER, product_id INTEGER,
        quantity INTEGER, subtotal REAL
    )
    """)
    cursor.executemany(
        "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
        [
            ("Sizzling Sisig", 199.0, 100, "meals"),
            ("Nachos",          80.0, 100, "snacks"),
            ("Gin Bilog",       85.0, 100, "alcohol"),
        ]
    )
    conn.commit()
    conn.close()

    yield temp_file.name

    try:
        os.unlink(temp_file.name)
    except PermissionError:
        pass


# ── Restock helpers (mirror ProductManagementSystem logic) ────────────────────

def get_low_stock_products(db_path, threshold=LOW_STOCK_THRESHOLD):
    """Return products at or below the stock threshold."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, price, stock, category FROM products WHERE stock <= ?",
        (threshold,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_restock_suggestions(db_path, threshold=LOW_STOCK_THRESHOLD):
    """
    Return restock suggestions combining low stock and sales popularity.
    Products are sorted by quantity sold (most popular first).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.name, p.stock, COALESCE(SUM(ti.quantity), 0) as total_sold
        FROM products p
        LEFT JOIN transaction_items ti ON p.id = ti.product_id
        WHERE p.stock <= ?
        GROUP BY p.id, p.name, p.stock
        ORDER BY total_sold DESC
    """, (threshold,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def restock_product(db_path, product_id, quantity):
    """Add stock to a product."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET stock = stock + ? WHERE id = ?",
        (quantity, product_id)
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_product_stock(db_path, product_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM products WHERE id=?", (product_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


# ── AC1: System suggests items when stock falls below threshold ────────────────

class TestLowStockDetection:
    """AC1: When stock levels fall below threshold, system suggests restocking."""

    def test_low_stock_products_are_detected(self, temp_db):
        low = get_low_stock_products(temp_db)
        assert len(low) > 0

    def test_correct_number_of_low_stock_products(self, temp_db):
        low = get_low_stock_products(temp_db)
        # Sizzling Sisig (5), Nachos (10), Gin Bilog (30) = 3 products
        assert len(low) == 3

    def test_sizzling_sisig_flagged_as_low_stock(self, temp_db):
        low = get_low_stock_products(temp_db)
        names = [r[1] for r in low]
        assert "Sizzling Sisig" in names

    def test_nachos_flagged_as_low_stock(self, temp_db):
        low = get_low_stock_products(temp_db)
        names = [r[1] for r in low]
        assert "Nachos" in names

    def test_product_at_threshold_is_flagged(self, temp_db):
        # Gin Bilog stock == 30 == threshold, should be flagged
        low = get_low_stock_products(temp_db)
        names = [r[1] for r in low]
        assert "Gin Bilog" in names

    def test_product_above_threshold_not_flagged(self, temp_db):
        low = get_low_stock_products(temp_db)
        names = [r[1] for r in low]
        assert "Fries - Cheese" not in names
        assert "Chocolate Milk Tea" not in names
        assert "Red Horse 1 Litro" not in names

    def test_no_suggestions_when_all_stock_sufficient(self, all_sufficient_db):
        low = get_low_stock_products(all_sufficient_db)
        assert low == []

    def test_low_stock_result_has_correct_columns(self, temp_db):
        low = get_low_stock_products(temp_db)
        for row in low:
            assert len(row) == 5  # id, name, price, stock, category

    def test_low_stock_values_are_at_or_below_threshold(self, temp_db):
        low = get_low_stock_products(temp_db)
        for row in low:
            assert row[3] <= LOW_STOCK_THRESHOLD

    def test_custom_threshold_works(self, temp_db):
        # With threshold=10, only Sizzling Sisig(5) and Nachos(10) flagged
        low = get_low_stock_products(temp_db, threshold=10)
        assert len(low) == 2

    def test_zero_stock_is_flagged(self, temp_db):
        # Insert a product with 0 stock
        conn = sqlite3.connect(temp_db)
        conn.execute("INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
                     ("Out of Stock Item", 50.0, 0, "snacks"))
        conn.commit()
        conn.close()
        low = get_low_stock_products(temp_db)
        names = [r[1] for r in low]
        assert "Out of Stock Item" in names

    def test_restock_removes_product_from_low_stock(self, temp_db):
        low_before = get_low_stock_products(temp_db)
        nachos = next(r for r in low_before if r[1] == "Nachos")
        restock_product(temp_db, nachos[0], 100)
        low_after = get_low_stock_products(temp_db)
        names_after = [r[1] for r in low_after]
        assert "Nachos" not in names_after

    def test_restock_increases_stock_correctly(self, temp_db):
        low = get_low_stock_products(temp_db)
        nachos = next(r for r in low if r[1] == "Nachos")
        original_stock = nachos[3]
        restock_product(temp_db, nachos[0], 50)
        new_stock = get_product_stock(temp_db, nachos[0])
        assert new_stock == original_stock + 50


# ── AC2: Restock recommendations displayed when viewing inventory ──────────────

class TestRestockRecommendations:
    """AC2: Restock recommendations are displayed when stock clerk views inventory."""

    def test_restock_suggestions_returned(self, temp_db):
        suggestions = get_restock_suggestions(temp_db)
        assert len(suggestions) > 0

    def test_suggestions_include_low_stock_products(self, temp_db):
        suggestions = get_restock_suggestions(temp_db)
        names = [r[1] for r in suggestions]
        assert "Sizzling Sisig" in names
        assert "Nachos" in names

    def test_suggestions_sorted_by_popularity(self, temp_db):
        suggestions = get_restock_suggestions(temp_db)
        # Sizzling Sisig (50 sold) should come before Nachos (40 sold)
        names = [r[1] for r in suggestions]
        assert names.index("Sizzling Sisig") < names.index("Nachos")

    def test_most_popular_low_stock_is_first(self, temp_db):
        suggestions = get_restock_suggestions(temp_db)
        assert suggestions[0][1] == "Sizzling Sisig"

    def test_suggestions_have_stock_info(self, temp_db):
        suggestions = get_restock_suggestions(temp_db)
        for r in suggestions:
            assert r[2] <= LOW_STOCK_THRESHOLD

    def test_suggestions_have_sales_data(self, temp_db):
        suggestions = get_restock_suggestions(temp_db)
        # Most popular items should have sales > 0
        assert suggestions[0][3] > 0

    def test_no_recommendations_when_stock_sufficient(self, all_sufficient_db):
        suggestions = get_restock_suggestions(all_sufficient_db)
        assert suggestions == []

    def test_sufficient_stock_products_excluded_from_suggestions(self, temp_db):
        suggestions = get_restock_suggestions(temp_db)
        names = [r[1] for r in suggestions]
        assert "Chocolate Milk Tea" not in names
        assert "Red Horse 1 Litro" not in names

    def test_suggestion_result_has_correct_columns(self, temp_db):
        suggestions = get_restock_suggestions(temp_db)
        for row in suggestions:
            assert len(row) == 4  # id, name, stock, total_sold

    def test_all_suggestions_are_below_threshold(self, temp_db):
        suggestions = get_restock_suggestions(temp_db)
        for r in suggestions:
            assert r[2] <= LOW_STOCK_THRESHOLD

    def test_restock_updates_reflected_in_suggestions(self, temp_db):
        suggestions_before = get_restock_suggestions(temp_db)
        sisig = next(r for r in suggestions_before if r[1] == "Sizzling Sisig")
        restock_product(temp_db, sisig[0], 200)
        suggestions_after = get_restock_suggestions(temp_db)
        names_after = [r[1] for r in suggestions_after]
        assert "Sizzling Sisig" not in names_after

    def test_product_with_no_sales_still_suggested_if_low_stock(self, temp_db):
        # Add a new product with low stock but no sales
        conn = sqlite3.connect(temp_db)
        conn.execute(
            "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
            ("New Item", 50.0, 5, "snacks")
        )
        conn.commit()
        conn.close()
        suggestions = get_restock_suggestions(temp_db)
        names = [r[1] for r in suggestions]
        assert "New Item" in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
