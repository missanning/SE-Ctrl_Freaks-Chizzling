import sqlite3

def connect_db():
    conn = sqlite3.connect("sales_inventory.db")
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
        ("Nachos", 80, 100),
        ("Shawarma Rice", 80, 100),

        # FRENCH FRIES
        ("Fries - Cheese", 50, 100),
        ("Fries - Barbeque", 50, 100),
        ("Fries - Sour and Cream", 50, 100),

        # TAKOYAKI
        ("Takoyaki - Cheese (5pcs)", 45, 100),
        ("Takoyaki - Ham and Cheese (5pcs)", 50, 100),
        ("Takoyaki - Crab (5pcs)", 50, 100),
        ("Takoyaki - Overload (7pcs)", 80, 100),

        # CHICKEN TENDERS RICE
        ("Chicken Tenders - Sour and Cream", 60, 100),
        ("Chicken Tenders - Barbeque", 60, 100),
        ("Chicken Tenders - Cheese", 60, 100),

        # BUNDLE MEALS
        ("Sizzling Tofu", 189, 100),
        ("Sizzling Liempo", 199, 100),
        ("Sizzling Sisig", 199, 100),

        # COMBO BUNDLE
        ("Sisig and Liempo", 199, 100),
        ("Sisig and Tofu", 199, 100),
        ("Liempo and Tofu", 199, 100),

        # SILOG
        ("Tocilog", 60, 100),
        ("Hotsilog", 60, 100),
        ("Chicksilog", 99, 100),
        ("Porksilog", 99, 100),
        ("Sisig Silog", 99, 100),

        # SIZZLING RICE MEALS
        ("Sizzling Sisig (Rice Meal)", 109, 100),
        ("Sizzling Tofu (Rice Meal)", 109, 100),
        ("Sizzling Liempo (Rice Meal)", 109, 100),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO products (name, price, stock) VALUES (?, ?, ?)",
        products
    )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    insert_default_data()
    print("Database setup completed successfully!")
