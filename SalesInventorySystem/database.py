import sqlite3

def connect_db():
    conn = sqlite3.connect("sales_inventory.db")
    cursor = conn.cursor()

    #Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER
    )
    """)

    # Transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Transaction items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        subtotal REAL
    )
    """)

    conn.commit()
    conn.close()

    def insert_default_data():
        conn = sqlite3.connect("sales_inventory.db")
        cursor = conn.cursor()

        # Insert Owner account
        cursor.execute("""
        INSERT OR IGNORE INTO users (username, password)
        VALUES ('owner', 'admin123')
        """)

        # Insert sample products
        products = [
            ("Coke", 20.0, 50),
            ("Bread", 35.0, 30),
            ("Milk", 50.0, 20),
            ("Eggs", 8.0, 100)
        ]

        for product in products:
            cursor.execute("""
            INSERT INTO products (name, price, stock)
            VALUES (?, ?, ?)
            """, product)

        conn.commit()
        conn.close()