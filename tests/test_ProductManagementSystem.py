import pytest
from database_setup import connect_db

def test_connect_db():
    conn = connect_db()
    assert conn is not None
    conn.close()

def test_products_table_exists():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
    result = cursor.fetchone()
    conn.close()
    assert result is not None

def test_insert_product():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (id, name, price, stock) VALUES (?, ?, ?, ?)", (999, "Test Product", 10.99, 50))
    conn.commit()
    cursor.execute("SELECT * FROM products WHERE id=?", (999,))
    result = cursor.fetchone()
    conn.close()
    assert result is not None
    assert result[1] == "Test Product"

def test_update_product():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name=?, price=?, stock=? WHERE id=?", ("Updated Product", 15.99, 75, 999))
    conn.commit()
    cursor.execute("SELECT * FROM products WHERE id=?", (999,))
    result = cursor.fetchone()
    conn.close()
    assert result[1] == "Updated Product"
    assert result[2] == 15.99
    assert result[3] == 75

def test_delete_product():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (999,))
    conn.commit()
    cursor.execute("SELECT * FROM products WHERE id=?", (999,))
    result = cursor.fetchone()
    conn.close()
    assert result is None

def test_search_product():
    # Insert a test product
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (id, name, price, stock) VALUES (?, ?, ?, ?)", (888, "Search Test", 5.00, 10))
    conn.commit()

    # Search for it
    cursor.execute("SELECT * FROM products WHERE id LIKE ? OR name LIKE ?", ('%888%', '%Search%'))
    results = cursor.fetchall()
    conn.close()
    assert len(results) > 0
    assert any(row[1] == "Search Test" for row in results)

    # Clean up
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (888,))
    conn.commit()
    conn.close()