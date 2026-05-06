# Test for US-10: Inventory Search

import pytest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Create a temp database with products across multiple categories."""
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
    cursor.executemany(
        "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
        [
            # meals
            ("Sizzling Sisig",         199.0, 100, "meals"),
            ("Sizzling Liempo",        199.0, 100, "meals"),
            ("Chicken silog",           99.0, 100, "meals"),
            # snacks
            ("Nachos",                  80.0, 100, "snacks"),
            ("Fries - Cheese",          50.0, 100, "snacks"),
            ("Takoyaki - Cheese (5pcs)",45.0, 100, "snacks"),
            # drinks
            ("Chocolate Milk Tea",      39.0, 100, "drinks"),
            ("Okinawa Milk Tea",        39.0, 100, "drinks"),
            # alcohol
            ("Red Horse 1 Litro",      150.0, 100, "alcohol"),
            ("Gin Bilog",               85.0, 100, "alcohol"),
        ]
    )
    conn.commit()
    conn.close()

    yield temp_file.name

    try:
        os.unlink(temp_file.name)
    except PermissionError:
        pass


# ── Inventory filter helpers ───────────────────────────────────────────────────

def get_all_products(db_path):
    """Return full inventory list (no filter)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, price, stock, category FROM products"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def filter_by_category(db_path, category):
    """Return products filtered by category."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if category.lower() in ("all", ""):
        cursor.execute(
            "SELECT id, name, price, stock, category FROM products"
        )
    else:
        cursor.execute(
            "SELECT id, name, price, stock, category FROM products WHERE LOWER(category) = ?",
            (category.lower(),)
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_by_name(db_path, keyword):
    """Return products matching a name keyword."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, price, stock, category FROM products WHERE name LIKE ?",
        (f"%{keyword}%",)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# ── AC1: Category filter shows only matching products ─────────────────────────

class TestCategoryFilter:
    """AC1: When a category filter is selected, only products in that category are shown."""

    def test_filter_meals_returns_only_meals(self, temp_db):
        results = filter_by_category(temp_db, "meals")
        assert all(r[4] == "meals" for r in results)

    def test_filter_snacks_returns_only_snacks(self, temp_db):
        results = filter_by_category(temp_db, "snacks")
        assert all(r[4] == "snacks" for r in results)

    def test_filter_drinks_returns_only_drinks(self, temp_db):
        results = filter_by_category(temp_db, "drinks")
        assert all(r[4] == "drinks" for r in results)

    def test_filter_alcohol_returns_only_alcohol(self, temp_db):
        results = filter_by_category(temp_db, "alcohol")
        assert all(r[4] == "alcohol" for r in results)

    def test_filter_meals_correct_count(self, temp_db):
        results = filter_by_category(temp_db, "meals")
        assert len(results) == 3

    def test_filter_snacks_correct_count(self, temp_db):
        results = filter_by_category(temp_db, "snacks")
        assert len(results) == 3

    def test_filter_drinks_correct_count(self, temp_db):
        results = filter_by_category(temp_db, "drinks")
        assert len(results) == 2

    def test_filter_alcohol_correct_count(self, temp_db):
        results = filter_by_category(temp_db, "alcohol")
        assert len(results) == 2

    def test_filter_meals_excludes_snacks(self, temp_db):
        results = filter_by_category(temp_db, "meals")
        categories = [r[4] for r in results]
        assert "snacks" not in categories

    def test_filter_meals_excludes_drinks(self, temp_db):
        results = filter_by_category(temp_db, "meals")
        categories = [r[4] for r in results]
        assert "drinks" not in categories

    def test_filter_snacks_excludes_alcohol(self, temp_db):
        results = filter_by_category(temp_db, "snacks")
        categories = [r[4] for r in results]
        assert "alcohol" not in categories

    def test_filter_is_case_insensitive(self, temp_db):
        lower = filter_by_category(temp_db, "meals")
        upper = filter_by_category(temp_db, "MEALS")
        assert len(lower) == len(upper)

    def test_filter_returns_correct_product_names(self, temp_db):
        results = filter_by_category(temp_db, "meals")
        names = [r[1] for r in results]
        assert "Sizzling Sisig" in names
        assert "Sizzling Liempo" in names
        assert "Chicken silog" in names

    def test_filter_nonexistent_category_returns_empty(self, temp_db):
        results = filter_by_category(temp_db, "desserts")
        assert results == []

    def test_filter_result_has_correct_columns(self, temp_db):
        results = filter_by_category(temp_db, "meals")
        for r in results:
            assert len(r) == 5  # id, name, price, stock, category

    def test_filter_returns_list(self, temp_db):
        results = filter_by_category(temp_db, "meals")
        assert isinstance(results, list)

    def test_filtered_products_have_positive_price(self, temp_db):
        results = filter_by_category(temp_db, "snacks")
        assert all(r[2] > 0 for r in results)

    def test_filtered_products_have_positive_stock(self, temp_db):
        results = filter_by_category(temp_db, "alcohol")
        assert all(r[3] > 0 for r in results)


# ── AC2: Clearing filter shows full inventory ─────────────────────────────────

class TestClearFilter:
    """AC2: When all categories are selected, the full inventory list is displayed."""

    def test_all_filter_returns_all_products(self, temp_db):
        results = filter_by_category(temp_db, "all")
        assert len(results) == 10

    def test_empty_string_filter_returns_all_products(self, temp_db):
        results = filter_by_category(temp_db, "")
        assert len(results) == 10

    def test_all_filter_includes_meals(self, temp_db):
        results = filter_by_category(temp_db, "all")
        categories = [r[4] for r in results]
        assert "meals" in categories

    def test_all_filter_includes_snacks(self, temp_db):
        results = filter_by_category(temp_db, "all")
        categories = [r[4] for r in results]
        assert "snacks" in categories

    def test_all_filter_includes_drinks(self, temp_db):
        results = filter_by_category(temp_db, "all")
        categories = [r[4] for r in results]
        assert "drinks" in categories

    def test_all_filter_includes_alcohol(self, temp_db):
        results = filter_by_category(temp_db, "all")
        categories = [r[4] for r in results]
        assert "alcohol" in categories

    def test_all_filter_count_matches_total(self, temp_db):
        all_products = get_all_products(temp_db)
        filtered_all = filter_by_category(temp_db, "all")
        assert len(filtered_all) == len(all_products)

    def test_all_filter_after_category_filter_restores_full_list(self, temp_db):
        filtered = filter_by_category(temp_db, "meals")
        assert len(filtered) == 3
        all_products = filter_by_category(temp_db, "all")
        assert len(all_products) == 10

    def test_all_filter_contains_all_unique_categories(self, temp_db):
        results = filter_by_category(temp_db, "all")
        categories = set(r[4] for r in results)
        assert categories == {"meals", "snacks", "drinks", "alcohol"}

    def test_all_filter_result_has_correct_columns(self, temp_db):
        results = filter_by_category(temp_db, "all")
        for r in results:
            assert len(r) == 5

    def test_search_by_name_returns_matching_products(self, temp_db):
        results = search_by_name(temp_db, "Sisig")
        names = [r[1] for r in results]
        assert "Sizzling Sisig" in names

    def test_search_by_name_partial_match(self, temp_db):
        results = search_by_name(temp_db, "Milk")
        assert len(results) == 2

    def test_search_by_name_no_match_returns_empty(self, temp_db):
        results = search_by_name(temp_db, "Pizza")
        assert results == []

    def test_search_by_name_case_insensitive(self, temp_db):
        lower = search_by_name(temp_db, "nachos")
        upper = search_by_name(temp_db, "NACHOS")
        assert len(lower) == len(upper)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
