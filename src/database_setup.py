import sqlite3
import os

def connect_db():
    db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
    return sqlite3.connect(db_path)


def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # PRODUCTS TABLE (MERGED: category + stock)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        price REAL,
        stock INTEGER,
        category TEXT
    )
    """)

    # Ensure missing columns exist
    cursor.execute("PRAGMA table_info(products)")
    columns = [row[1] for row in cursor.fetchall()]

    if "category" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'unknown'")

    if "stock" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0")

    # PRODUCT ARCHIVE TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER
    )
    """)

    # INGREDIENTS ARCHIVE TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        stock REAL,
        unit TEXT
    )
    """)

    # TRANSACTIONS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL,
        payment REAL,
        change REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # TRANSACTION ITEMS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        subtotal REAL,
        FOREIGN KEY(transaction_id) REFERENCES transactions(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    # INGREDIENTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        stock REAL,
        unit TEXT
    )
    """)

    # RECIPE TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipe_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        ingredient_name TEXT,
        quantity REAL,
        unit TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_default_data():
    conn = connect_db()
    cursor = conn.cursor()

    # USERS
    users = [
        ("cashier", "1234", "cashier"),
        ("inventory_staff", "1234", "inventory_staff"),
        ("admin", "1234", "owner")
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        users
    )

    # PRODUCTS (now includes stock + category)
    products = [
        ("Nachos", 80, 100, "snacks"),
        ("Fries - Cheese", 50, 100, "snacks"),
        ("Chicken Tenders", 70, 100, "meals"),
        ("Sisig Silog", 109, 100, "meals"),
        ("Red Horse 1 Litro", 150, 100, "alcohol"),
        ("Chocolate Milk Tea", 39, 100, "drinks"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
        products
    )

    # INGREDIENTS
    ingredients = [
        ("Pork", 5000, "grams"),
        ("Egg", 200, "pcs"),
        ("Cheese", 100, "slices")
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO ingredients (name, stock, unit) VALUES (?, ?, ?)",
        ingredients
    )

    conn.commit()
    conn.close()


def prompt_success():
    print("\n" + "="*50)
    print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("="*50)


if __name__ == "__main__":
    create_tables()
    insert_default_data()
    prompt_success()