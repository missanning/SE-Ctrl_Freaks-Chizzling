import pytest
from database_setup import connect_db

def test_connect_db():
    conn = connect_db()
    assert conn is not None
    conn.close()

def test_ingredients_table_exists():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingredients'")
    result = cursor.fetchone()
    conn.close()
    assert result is not None

def test_insert_ingredient():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ingredients (name, stock, unit) VALUES (?, ?, ?)", ("Test Ingredient", 100.0, "kg"))
    conn.commit()
    cursor.execute("SELECT * FROM ingredients WHERE name=?", ("Test Ingredient",))
    result = cursor.fetchone()
    conn.close()
    assert result is not None
    assert result[1] == "Test Ingredient"

def test_delete_ingredient():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ingredients WHERE name=?", ("Test Ingredient",))
    conn.commit()
    cursor.execute("SELECT * FROM ingredients WHERE name=?", ("Test Ingredient",))
    result = cursor.fetchone()
    conn.close()
    assert result is None