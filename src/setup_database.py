import sqlite3

def connect_db():
    import os
    db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
    conn = sqlite3.connect(db_path)
    return conn

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # Users table (Cashier / Owner)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        category TEXT,
        stock INTEGER
    )
    """)

    # Transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL,
        payment REAL,
        change REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Transaction Items table
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

    conn.commit()
    conn.close()

def insert_default_data():
    conn = connect_db()
    cursor = conn.cursor()

    # Insert default user
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                   ("cashier", "1234", "cashier"))

    products = [

        # SNACKS
        ("Nachos", 80, "Snacks", 100),
        ("Shawarma Rice", 80, "Snacks", 100),

        # FRENCH FRIES
        ("Fries - Cheese", 50, "Snacks", 100),
        ("Fries - Barbeque", 50, "Snacks", 100),
        ("Fries - Sour and Cream", 50, "Snacks", 100),

        # TAKOYAKI
        ("Takoyaki - Cheese (5pcs)", 45, "Snacks", 100),
        ("Takoyaki - Ham and Cheese (5pcs)", 50, "Snacks", 100),
        ("Takoyaki - Crab (5pcs)", 50, "Snacks", 100),
        ("Takoyaki - Overload (7pcs)", 80, "Snacks", 100),

        # CHICKEN TENDERS RICE
        ("Chicken Tenders - Sour and Cream", 60, "Meals", 100),
        ("Chicken Tenders - Barbeque", 60, "Meals", 100),
        ("Chicken Tenders - Cheese", 60, "Meals", 100),

        # BUNDLE MEALS
        ("Sizzling Tofu", 189, "Meals", 100),
        ("Sizzling Liempo", 199, "Meals", 100),
        ("Sizzling Sisig", 199, "Meals", 100),

        # COMBO BUNDLE
        ("Sisig and Liempo", 199, "Meals", 100),
        ("Sisig and Tofu", 199, "Meals", 100),
        ("Liempo and Tofu", 199, "Meals", 100),

        # SILOG
        ("Tocilog", 60, "Meals", 100),
        ("Hotsilog", 60, "Meals", 100),
        ("Chicksilog", 99, "Meals", 100),
        ("Porksilog", 99, "Meals", 100),
        ("Sisig Silog", 99, "Meals", 100),

        # SIZZLING RICE MEALS
        ("Sizzling Sisig (Rice Meal)", 109, "Meals", 100),
        ("Sizzling Tofu (Rice Meal)", 109, "Meals", 100),
        ("Sizzling Liempo (Rice Meal)", 109, "Meals", 100),

        # DRINKS
        ("Water", 15, "Drinks", 100),
        ("Iced Tea (1 Pitcher)", 50, "Drinks", 100),
        ("Coca Cola", 50, "Drinks", 100),
        ("Pepsi", 50, "Drinks", 100),
        ("Royal", 50, "Drinks", 100),
        ("Sprite", 50, "Drinks", 100),
        ("Mountain Dew", 50, "Drinks", 100),

        # ALCOHOL
        ("Red Wine", 250, "Alcohol", 50),
        ("Beer (Bottle)", 120, "Alcohol", 50),
    ]

    # Ensure category column exists before inserting (supports legacy DBs)
    cursor.execute("PRAGMA table_info(products)")
    columns = [row[1] for row in cursor.fetchall()]
    has_category = "category" in columns
    if not has_category:
        cursor.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'All'")
        conn.commit()
        has_category = True

    if has_category:
        insert_query = "INSERT OR IGNORE INTO products (name, price, category, stock) VALUES (?, ?, ?, ?)"
        insert_data = products
    else:
        insert_query = "INSERT OR IGNORE INTO products (name, price, stock) VALUES (?, ?, ?)"
        insert_data = [(name, price, stock) for name, price, category, stock in products]

    cursor.executemany(insert_query, insert_data)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    insert_default_data()
    print("Database setup completed successfully!")
