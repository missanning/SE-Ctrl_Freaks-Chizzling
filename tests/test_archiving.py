# Test for US-09: Product and Ingredient Archiving


import pytest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Create a temp database with products, ingredients, and archive tables."""
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
    CREATE TABLE product_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, price REAL, stock INTEGER, category TEXT,
        archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE, stock REAL, unit TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE ingredients_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, stock REAL, unit TEXT,
        archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    cursor.executemany(
        "INSERT INTO ingredients (name, stock, unit) VALUES (?, ?, ?)",
        [
            ("Pork",        5000, "grams"),
            ("Egg",          200, "pcs"),
            ("Butter",       500, "grams"),
        ]
    )

    conn.commit()
    conn.close()

    yield temp_file.name

    try:
        os.unlink(temp_file.name)
    except PermissionError:
        pass


# ── DB helpers ─────────────────────────────────────────────────────────────────

def get_active_products(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock, category FROM products")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_archived_products(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM product_archive")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_active_ingredients(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, stock, unit FROM ingredients")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_archived_ingredients(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, stock, unit FROM ingredients_archive")
    rows = cursor.fetchall()
    conn.close()
    return rows

def archive_product(db_path, keyword):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id=? OR name=?", (keyword, keyword))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    cursor.execute("""
        INSERT INTO product_archive (name, price, stock, category)
        SELECT name, price, stock, category FROM products WHERE id=? OR name=?
    """, (keyword, keyword))
    cursor.execute("DELETE FROM products WHERE id=? OR name=?", (keyword, keyword))
    conn.commit()
    conn.close()
    return True

def archive_ingredient(db_path, keyword):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ingredients WHERE id=? OR name=?", (keyword, keyword))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    cursor.execute("""
        INSERT INTO ingredients_archive (name, stock, unit)
        SELECT name, stock, unit FROM ingredients WHERE id=? OR name=?
    """, (keyword, keyword))
    cursor.execute("DELETE FROM ingredients WHERE id=? OR name=?", (keyword, keyword))
    conn.commit()
    conn.close()
    return True

def unarchive_product(db_path, keyword):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product_archive WHERE id=? OR name=?", (keyword, keyword))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    cursor.execute("""
        INSERT INTO products (name, price, stock, category)
        SELECT name, price, stock, category FROM product_archive WHERE id=? OR name=?
    """, (keyword, keyword))
    cursor.execute("DELETE FROM product_archive WHERE id=? OR name=?", (keyword, keyword))
    conn.commit()
    conn.close()
    return True

def unarchive_ingredient(db_path, keyword):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ingredients_archive WHERE id=? OR name=?", (keyword, keyword))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    cursor.execute("""
        INSERT INTO ingredients (name, stock, unit)
        SELECT name, stock, unit FROM ingredients_archive WHERE id=? OR name=?
    """, (keyword, keyword))
    cursor.execute("DELETE FROM ingredients_archive WHERE id=? OR name=?", (keyword, keyword))
    conn.commit()
    conn.close()
    return True

def delete_archived_product(db_path, keyword):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product_archive WHERE id=? OR name=?", (keyword, keyword))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    cursor.execute("DELETE FROM product_archive WHERE id=? OR name=?", (keyword, keyword))
    conn.commit()
    conn.close()
    return True

def delete_archived_ingredient(db_path, keyword):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ingredients_archive WHERE id=? OR name=?", (keyword, keyword))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    cursor.execute("DELETE FROM ingredients_archive WHERE id=? OR name=?", (keyword, keyword))
    conn.commit()
    conn.close()
    return True

def search_archive(db_path, table, keyword):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM {table} WHERE id LIKE ? OR name LIKE ?",
        (f"%{keyword}%", f"%{keyword}%")
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# ── AC1: Archive moves item out of active list ────────────────────────────────

class TestArchiveProduct:
    """AC1: Archiving a product moves it to archive and removes from active list."""

    def test_archive_product_returns_true(self, temp_db):
        assert archive_product(temp_db, "Nachos") is True

    def test_archived_product_removed_from_active(self, temp_db):
        archive_product(temp_db, "Nachos")
        names = [p[1] for p in get_active_products(temp_db)]
        assert "Nachos" not in names

    def test_archived_product_appears_in_archive(self, temp_db):
        archive_product(temp_db, "Nachos")
        names = [p[1] for p in get_archived_products(temp_db)]
        assert "Nachos" in names

    def test_active_count_decreases_after_archive(self, temp_db):
        before = len(get_active_products(temp_db))
        archive_product(temp_db, "Nachos")
        after = len(get_active_products(temp_db))
        assert after == before - 1

    def test_archive_count_increases_after_archive(self, temp_db):
        before = len(get_archived_products(temp_db))
        archive_product(temp_db, "Nachos")
        after = len(get_archived_products(temp_db))
        assert after == before + 1

    def test_archive_product_by_name(self, temp_db):
        archive_product(temp_db, "Nachos")
        names = [p[1] for p in get_archived_products(temp_db)]
        assert "Nachos" in names

    def test_archive_nonexistent_product_returns_false(self, temp_db):
        assert archive_product(temp_db, "Ghost Product") is False

    def test_other_products_unaffected_after_archive(self, temp_db):
        archive_product(temp_db, "Nachos")
        names = [p[1] for p in get_active_products(temp_db)]
        assert "Sizzling Sisig" in names
        assert "Gin Bilog" in names

    def test_archived_product_retains_correct_data(self, temp_db):
        archive_product(temp_db, "Nachos")
        archived = get_archived_products(temp_db)
        nachos = next(r for r in archived if r[1] == "Nachos")
        assert nachos[2] == 80.0
        assert nachos[3] == 100

    def test_archive_multiple_products(self, temp_db):
        archive_product(temp_db, "Nachos")
        archive_product(temp_db, "Gin Bilog")
        archived_names = [p[1] for p in get_archived_products(temp_db)]
        assert "Nachos" in archived_names
        assert "Gin Bilog" in archived_names


class TestArchiveIngredient:
    """AC1: Archiving an ingredient moves it to archive and removes from active list."""

    def test_archive_ingredient_returns_true(self, temp_db):
        assert archive_ingredient(temp_db, "Egg") is True

    def test_archived_ingredient_removed_from_active(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        names = [i[1] for i in get_active_ingredients(temp_db)]
        assert "Egg" not in names

    def test_archived_ingredient_appears_in_archive(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        names = [i[1] for i in get_archived_ingredients(temp_db)]
        assert "Egg" in names

    def test_active_ingredient_count_decreases(self, temp_db):
        before = len(get_active_ingredients(temp_db))
        archive_ingredient(temp_db, "Egg")
        after = len(get_active_ingredients(temp_db))
        assert after == before - 1

    def test_archive_nonexistent_ingredient_returns_false(self, temp_db):
        assert archive_ingredient(temp_db, "Ghost Ingredient") is False

    def test_archived_ingredient_retains_correct_data(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        archived = get_archived_ingredients(temp_db)
        egg = next(r for r in archived if r[1] == "Egg")
        assert egg[2] == 200
        assert egg[3] == "pcs"


# ── AC2: View, search, and delete archived records ────────────────────────────

class TestViewAndSearchArchive:
    """AC2: Staff can view, search, and permanently delete archived records."""

    def test_archived_products_are_viewable(self, temp_db):
        archive_product(temp_db, "Nachos")
        archived = get_archived_products(temp_db)
        assert len(archived) > 0

    def test_archived_ingredients_are_viewable(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        archived = get_archived_ingredients(temp_db)
        assert len(archived) > 0

    def test_search_archived_product_by_name(self, temp_db):
        archive_product(temp_db, "Nachos")
        results = search_archive(temp_db, "product_archive", "Nachos")
        assert len(results) > 0
        assert results[0][1] == "Nachos"

    def test_search_archived_product_partial_match(self, temp_db):
        archive_product(temp_db, "Nachos")
        results = search_archive(temp_db, "product_archive", "Nach")
        assert len(results) > 0

    def test_search_archived_ingredient_by_name(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        results = search_archive(temp_db, "ingredients_archive", "Egg")
        assert len(results) > 0

    def test_search_returns_empty_for_no_match(self, temp_db):
        archive_product(temp_db, "Nachos")
        results = search_archive(temp_db, "product_archive", "Pizza")
        assert results == []

    def test_delete_archived_product_returns_true(self, temp_db):
        archive_product(temp_db, "Nachos")
        assert delete_archived_product(temp_db, "Nachos") is True

    def test_deleted_archived_product_not_in_archive(self, temp_db):
        archive_product(temp_db, "Nachos")
        delete_archived_product(temp_db, "Nachos")
        names = [p[1] for p in get_archived_products(temp_db)]
        assert "Nachos" not in names

    def test_deleted_archived_product_not_in_active(self, temp_db):
        archive_product(temp_db, "Nachos")
        delete_archived_product(temp_db, "Nachos")
        names = [p[1] for p in get_active_products(temp_db)]
        assert "Nachos" not in names

    def test_delete_archived_ingredient_returns_true(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        assert delete_archived_ingredient(temp_db, "Egg") is True

    def test_deleted_archived_ingredient_not_in_archive(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        delete_archived_ingredient(temp_db, "Egg")
        names = [i[1] for i in get_archived_ingredients(temp_db)]
        assert "Egg" not in names

    def test_delete_nonexistent_archived_product_returns_false(self, temp_db):
        assert delete_archived_product(temp_db, "Ghost") is False

    def test_delete_nonexistent_archived_ingredient_returns_false(self, temp_db):
        assert delete_archived_ingredient(temp_db, "Ghost") is False


# ── AC3: Unarchive restores item to active list ───────────────────────────────

class TestUnarchiveProduct:
    """AC3: Unarchiving restores a product back to the active list."""

    def test_unarchive_product_returns_true(self, temp_db):
        archive_product(temp_db, "Nachos")
        assert unarchive_product(temp_db, "Nachos") is True

    def test_unarchived_product_appears_in_active(self, temp_db):
        archive_product(temp_db, "Nachos")
        unarchive_product(temp_db, "Nachos")
        names = [p[1] for p in get_active_products(temp_db)]
        assert "Nachos" in names

    def test_unarchived_product_removed_from_archive(self, temp_db):
        archive_product(temp_db, "Nachos")
        unarchive_product(temp_db, "Nachos")
        names = [p[1] for p in get_archived_products(temp_db)]
        assert "Nachos" not in names

    def test_active_count_restored_after_unarchive(self, temp_db):
        original = len(get_active_products(temp_db))
        archive_product(temp_db, "Nachos")
        unarchive_product(temp_db, "Nachos")
        restored = len(get_active_products(temp_db))
        assert restored == original

    def test_unarchive_nonexistent_returns_false(self, temp_db):
        assert unarchive_product(temp_db, "Ghost") is False

    def test_unarchived_product_retains_correct_price(self, temp_db):
        archive_product(temp_db, "Nachos")
        unarchive_product(temp_db, "Nachos")
        products = get_active_products(temp_db)
        nachos = next(p for p in products if p[1] == "Nachos")
        assert nachos[2] == 80.0

    def test_unarchived_product_retains_correct_stock(self, temp_db):
        archive_product(temp_db, "Nachos")
        unarchive_product(temp_db, "Nachos")
        products = get_active_products(temp_db)
        nachos = next(p for p in products if p[1] == "Nachos")
        assert nachos[3] == 100

    def test_archive_count_decreases_after_unarchive(self, temp_db):
        archive_product(temp_db, "Nachos")
        before = len(get_archived_products(temp_db))
        unarchive_product(temp_db, "Nachos")
        after = len(get_archived_products(temp_db))
        assert after == before - 1


class TestUnarchiveIngredient:
    """AC3: Unarchiving restores an ingredient back to the active list."""

    def test_unarchive_ingredient_returns_true(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        assert unarchive_ingredient(temp_db, "Egg") is True

    def test_unarchived_ingredient_appears_in_active(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        unarchive_ingredient(temp_db, "Egg")
        names = [i[1] for i in get_active_ingredients(temp_db)]
        assert "Egg" in names

    def test_unarchived_ingredient_removed_from_archive(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        unarchive_ingredient(temp_db, "Egg")
        names = [i[1] for i in get_archived_ingredients(temp_db)]
        assert "Egg" not in names

    def test_unarchive_nonexistent_ingredient_returns_false(self, temp_db):
        assert unarchive_ingredient(temp_db, "Ghost") is False

    def test_unarchived_ingredient_retains_correct_data(self, temp_db):
        archive_ingredient(temp_db, "Egg")
        unarchive_ingredient(temp_db, "Egg")
        ingredients = get_active_ingredients(temp_db)
        egg = next(i for i in ingredients if i[1] == "Egg")
        assert egg[2] == 200
        assert egg[3] == "pcs"

    def test_active_ingredient_count_restored_after_unarchive(self, temp_db):
        original = len(get_active_ingredients(temp_db))
        archive_ingredient(temp_db, "Egg")
        unarchive_ingredient(temp_db, "Egg")
        restored = len(get_active_ingredients(temp_db))
        assert restored == original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
