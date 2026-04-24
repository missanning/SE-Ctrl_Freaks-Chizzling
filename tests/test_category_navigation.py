# Test for US-11: Category Navigation
# Test Objective: Ensure that category buttons correctly filter products by category,
# "All" shows every item, default view loads all items, and empty categories show nothing.

import pytest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def temp_db():
    """Create a temp database with categorized products."""
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

    products = [
        ("Sizzling Sisig",       199.0, "meals"),
        ("Sizzling Liempo",      199.0, "meals"),
        ("Nachos",                80.0, "snacks"),
        ("Fries - Cheese",        50.0, "snacks"),
        ("Chocolate Milk Tea",    39.0, "drinks"),
        ("Okinawa Milk Tea",      39.0, "drinks"),
        ("Red Horse 1 Litro",    150.0, "alcohol"),
        ("Gin Bilog",             85.0, "alcohol"),
    ]

    cursor.executemany(
        "INSERT INTO products (name, price, category) VALUES (?, ?, ?)", products
    )
    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


def load_products(db_path, category=None):
    """Simulate ChizzlingPOS.load_products() logic."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if category and category.lower() not in ("all", ""):
        cursor.execute(
            "SELECT id, name, price, COALESCE(category, 'All') FROM products WHERE LOWER(category)=?",
            (category.lower(),)
        )
    else:
        cursor.execute(
            "SELECT id, name, price, COALESCE(category, 'All') FROM products"
        )

    products = cursor.fetchall()
    conn.close()
    return products


class TestCategoryFilter:
    """AC1: Display items by selected category"""

    def test_meals_category_returns_only_meals(self, temp_db):
        products = load_products(temp_db, "meals")
        assert len(products) == 2
        assert all(p[3] == "meals" for p in products)

    def test_snacks_category_returns_only_snacks(self, temp_db):
        products = load_products(temp_db, "snacks")
        assert len(products) == 2
        assert all(p[3] == "snacks" for p in products)

    def test_drinks_category_returns_only_drinks(self, temp_db):
        products = load_products(temp_db, "drinks")
        assert len(products) == 2
        assert all(p[3] == "drinks" for p in products)

    def test_alcohol_category_returns_only_alcohol(self, temp_db):
        products = load_products(temp_db, "alcohol")
        assert len(products) == 2
        assert all(p[3] == "alcohol" for p in products)

    def test_meals_does_not_contain_snacks(self, temp_db):
        products = load_products(temp_db, "meals")
        names = [p[1] for p in products]
        assert "Nachos" not in names
        assert "Fries - Cheese" not in names

    def test_category_filter_is_case_insensitive(self, temp_db):
        lower = load_products(temp_db, "meals")
        upper = load_products(temp_db, "MEALS")
        assert len(lower) == len(upper)


class TestShowAllItems:
    """AC2: Show all items when 'All' is selected"""

    def test_all_category_returns_every_product(self, temp_db):
        products = load_products(temp_db, "all")
        assert len(products) == 8

    def test_all_category_contains_every_category(self, temp_db):
        products = load_products(temp_db, "all")
        categories = {p[3] for p in products}
        assert categories == {"meals", "snacks", "drinks", "alcohol"}

    def test_none_returns_all_products(self, temp_db):
        """Passing None (default) should also return all products."""
        products = load_products(temp_db, None)
        assert len(products) == 8

    def test_empty_string_returns_all_products(self, temp_db):
        products = load_products(temp_db, "")
        assert len(products) == 8


class TestDefaultCategoryView:
    """AC3: Default category view loads all items"""

    def test_default_load_returns_all_products(self, temp_db):
        """No category passed = default load = all products shown."""
        products = load_products(temp_db)
        assert len(products) == 8

    def test_default_load_includes_all_categories(self, temp_db):
        products = load_products(temp_db)
        categories = {p[3] for p in products}
        assert "meals" in categories
        assert "snacks" in categories
        assert "drinks" in categories
        assert "alcohol" in categories


class TestEmptyCategory:
    """AC4: No items available in category shows blank"""

    def test_nonexistent_category_returns_empty(self, temp_db):
        products = load_products(temp_db, "desserts")
        assert len(products) == 0

    def test_empty_result_is_empty_list(self, temp_db):
        products = load_products(temp_db, "desserts")
        assert products == []

    def test_category_with_no_products_after_deletion(self, temp_db):
        """Remove all meals and verify meals category returns empty."""
        conn = sqlite3.connect(temp_db)
        conn.execute("DELETE FROM products WHERE category='meals'")
        conn.commit()
        conn.close()

        products = load_products(temp_db, "meals")
        assert len(products) == 0


if __name__ == "__main__":
    pytest.main([__file__])
