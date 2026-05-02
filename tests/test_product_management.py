# Test for US-03: Product Management


import pytest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Create a temp database with a products table and sample data."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE products (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        price REAL,
        stock INTEGER,
        category TEXT
    )
    """)
    cursor.executemany(
        "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
        [
            ("Sizzling Sisig",  199.0, 100, "meals"),
            ("Nachos",           80.0, 100, "snacks"),
            ("Gin Bilog",        85.0, 100, "alcohol"),
        ]
    )
    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def empty_db():
    """Create a temp database with an empty products table."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE products (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        price REAL,
        stock INTEGER,
        category TEXT
    )
    """)
    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


# ── DB helpers (mirror ProductManagementSystem logic) ─────────────────────────

def get_all_products(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock, category FROM products")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_product_by_name(db_path, name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock, category FROM products WHERE name=?", (name,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_product_by_id(db_path, product_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock, category FROM products WHERE id=?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def add_product(db_path, name, price, stock, category):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products WHERE name=?", (name,))
    if cursor.fetchone():
        conn.close()
        return False  # duplicate
    cursor.execute(
        "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
        (name, price, stock, category)
    )
    conn.commit()
    conn.close()
    return True


def edit_product(db_path, product_id, name=None, price=None, stock=None, category=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, stock, category FROM products WHERE id=?", (product_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    cur_name, cur_price, cur_stock, cur_cat = result
    cursor.execute(
        "UPDATE products SET name=?, price=?, stock=?, category=? WHERE id=?",
        (name or cur_name, price or cur_price, stock or cur_stock, category or cur_cat, product_id)
    )
    conn.commit()
    conn.close()
    return True


def delete_product(db_path, product_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products WHERE id=?", (product_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()
    return True


# ── AC1: Add product ──────────────────────────────────────────────────────────

class TestAddProduct:
    """AC1: When a new product is added with valid details,
    it appears in the product list."""

    def test_add_product_returns_true_on_success(self, temp_db):
        result = add_product(temp_db, "Takoyaki", 45.0, 100, "snacks")
        assert result is True

    def test_added_product_appears_in_list(self, temp_db):
        add_product(temp_db, "Takoyaki", 45.0, 100, "snacks")
        products = get_all_products(temp_db)
        names = [p[1] for p in products]
        assert "Takoyaki" in names

    def test_added_product_has_correct_name(self, temp_db):
        add_product(temp_db, "Takoyaki", 45.0, 100, "snacks")
        product = get_product_by_name(temp_db, "Takoyaki")
        assert product[1] == "Takoyaki"

    def test_added_product_has_correct_price(self, temp_db):
        add_product(temp_db, "Takoyaki", 45.0, 100, "snacks")
        product = get_product_by_name(temp_db, "Takoyaki")
        assert product[2] == 45.0

    def test_added_product_has_correct_stock(self, temp_db):
        add_product(temp_db, "Takoyaki", 45.0, 100, "snacks")
        product = get_product_by_name(temp_db, "Takoyaki")
        assert product[3] == 100

    def test_added_product_has_correct_category(self, temp_db):
        add_product(temp_db, "Takoyaki", 45.0, 100, "snacks")
        product = get_product_by_name(temp_db, "Takoyaki")
        assert product[4] == "snacks"

    def test_product_count_increases_after_add(self, temp_db):
        before = len(get_all_products(temp_db))
        add_product(temp_db, "Takoyaki", 45.0, 100, "snacks")
        after = len(get_all_products(temp_db))
        assert after == before + 1

    def test_add_multiple_products(self, temp_db):
        add_product(temp_db, "Takoyaki", 45.0, 100, "snacks")
        add_product(temp_db, "Shawarma Rice", 80.0, 100, "snacks")
        products = get_all_products(temp_db)
        names = [p[1] for p in products]
        assert "Takoyaki" in names
        assert "Shawarma Rice" in names

    def test_add_product_to_empty_db(self, empty_db):
        add_product(empty_db, "Nachos", 80.0, 100, "snacks")
        products = get_all_products(empty_db)
        assert len(products) == 1
        assert products[0][1] == "Nachos"

    def test_duplicate_product_not_added(self, temp_db):
        result = add_product(temp_db, "Nachos", 80.0, 100, "snacks")
        assert result is False

    def test_duplicate_product_does_not_increase_count(self, temp_db):
        before = len(get_all_products(temp_db))
        add_product(temp_db, "Nachos", 80.0, 100, "snacks")
        after = len(get_all_products(temp_db))
        assert after == before

    def test_added_product_has_assigned_id(self, temp_db):
        add_product(temp_db, "Takoyaki", 45.0, 100, "snacks")
        product = get_product_by_name(temp_db, "Takoyaki")
        assert product[0] is not None
        assert isinstance(product[0], int)


# ── AC2: Edit product ─────────────────────────────────────────────────────────

class TestEditProduct:
    """AC2: When the stock clerk edits product details,
    changes are saved and reflected immediately."""

    def test_edit_product_returns_true_on_success(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        result = edit_product(temp_db, product[0], price=90.0)
        assert result is True

    def test_edited_price_is_reflected(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        edit_product(temp_db, product[0], price=90.0)
        updated = get_product_by_id(temp_db, product[0])
        assert updated[2] == 90.0

    def test_edited_name_is_reflected(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        edit_product(temp_db, product[0], name="Nachos Deluxe")
        updated = get_product_by_id(temp_db, product[0])
        assert updated[1] == "Nachos Deluxe"

    def test_edited_stock_is_reflected(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        edit_product(temp_db, product[0], stock=50)
        updated = get_product_by_id(temp_db, product[0])
        assert updated[3] == 50

    def test_edited_category_is_reflected(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        edit_product(temp_db, product[0], category="meals")
        updated = get_product_by_id(temp_db, product[0])
        assert updated[4] == "meals"

    def test_unedited_fields_remain_unchanged(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        original_name = product[1]
        original_stock = product[3]
        edit_product(temp_db, product[0], price=90.0)
        updated = get_product_by_id(temp_db, product[0])
        assert updated[1] == original_name
        assert updated[3] == original_stock

    def test_edit_nonexistent_product_returns_false(self, temp_db):
        result = edit_product(temp_db, 9999, price=50.0)
        assert result is False

    def test_edit_multiple_fields_at_once(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        edit_product(temp_db, product[0], name="Nachos XL", price=100.0, stock=80)
        updated = get_product_by_id(temp_db, product[0])
        assert updated[1] == "Nachos XL"
        assert updated[2] == 100.0
        assert updated[3] == 80

    def test_product_count_unchanged_after_edit(self, temp_db):
        before = len(get_all_products(temp_db))
        product = get_product_by_name(temp_db, "Nachos")
        edit_product(temp_db, product[0], price=90.0)
        after = len(get_all_products(temp_db))
        assert before == after

    def test_edit_is_immediately_reflected_in_list(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        edit_product(temp_db, product[0], price=95.0)
        products = get_all_products(temp_db)
        nachos = next(p for p in products if p[1] == "Nachos")
        assert nachos[2] == 95.0


# ── AC3: Delete product ───────────────────────────────────────────────────────

class TestDeleteProduct:
    """AC3: When the stock clerk deletes a product,
    it is removed from the system."""

    def test_delete_product_returns_true_on_success(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        result = delete_product(temp_db, product[0])
        assert result is True

    def test_deleted_product_not_in_list(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        delete_product(temp_db, product[0])
        products = get_all_products(temp_db)
        names = [p[1] for p in products]
        assert "Nachos" not in names

    def test_product_count_decreases_after_delete(self, temp_db):
        before = len(get_all_products(temp_db))
        product = get_product_by_name(temp_db, "Nachos")
        delete_product(temp_db, product[0])
        after = len(get_all_products(temp_db))
        assert after == before - 1

    def test_deleted_product_cannot_be_fetched_by_id(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        pid = product[0]
        delete_product(temp_db, pid)
        result = get_product_by_id(temp_db, pid)
        assert result is None

    def test_delete_nonexistent_product_returns_false(self, temp_db):
        result = delete_product(temp_db, 9999)
        assert result is False

    def test_other_products_unaffected_after_delete(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        delete_product(temp_db, product[0])
        products = get_all_products(temp_db)
        names = [p[1] for p in products]
        assert "Sizzling Sisig" in names
        assert "Gin Bilog" in names

    def test_delete_all_products_results_in_empty_list(self, temp_db):
        for product in get_all_products(temp_db):
            delete_product(temp_db, product[0])
        assert get_all_products(temp_db) == []

    def test_deleted_product_can_be_re_added(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        delete_product(temp_db, product[0])
        result = add_product(temp_db, "Nachos", 80.0, 100, "snacks")
        assert result is True
        assert get_product_by_name(temp_db, "Nachos") is not None

    def test_delete_is_immediately_reflected_in_list(self, temp_db):
        product = get_product_by_name(temp_db, "Nachos")
        delete_product(temp_db, product[0])
        products = get_all_products(temp_db)
        assert all(p[1] != "Nachos" for p in products)

    def test_delete_multiple_products(self, temp_db):
        for name in ["Nachos", "Gin Bilog"]:
            product = get_product_by_name(temp_db, name)
            delete_product(temp_db, product[0])
        products = get_all_products(temp_db)
        names = [p[1] for p in products]
        assert "Nachos" not in names
        assert "Gin Bilog" not in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
