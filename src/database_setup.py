import sqlite3

def connect_db():
    conn = sqlite3.connect("sales_inventory.db")
    return conn


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

    # PRODUCTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
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

    # PRODUCT ARCHIVE TABLE (ADDED)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER
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

    # INGREDIENTS TABLE (Inventory)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        stock REAL,
        unit TEXT
    )
    """)

    # RECIPE TABLE (ingredient usage per product)
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

    # DEFAULT USERS
    users = [
        ("cashier", "1234", "cashier"),
        ("Staff_1", "1234", "inventory_staff"),
        ("Admin_1", "1234", "admin_staff")
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        users
    )

    # PRODUCTS
    products = [

        ("Nachos", 80, 100),
        ("Shawarma Rice", 80, 100),

        ("Fries - Cheese", 50, 100),
        ("Fries - Barbeque", 50, 100),
        ("Fries - Sour and Cream", 50, 100),

        ("Takoyaki - Cheese (5pcs)", 45, 100),
        ("Takoyaki - Ham and Cheese (5pcs)", 50, 100),
        ("Takoyaki - Crab (5pcs)", 50, 100),
        ("Takoyaki - Overload (7pcs)", 80, 100),

        ("Chicken Tenders - Sour and Cream", 60, 100),
        ("Chicken Tenders - Barbeque", 60, 100),
        ("Chicken Tenders - Cheese", 60, 100),

        ("Sizzling Tofu", 189, 100),
        ("Sizzling Liempo", 199, 100),
        ("Sizzling Sisig", 199, 100),

        ("Sisig and Liempo", 199, 100),
        ("Sisig and Tofu", 199, 100),
        ("Liempo and Tofu", 199, 100),

        ("Tocilog", 60, 100),
        ("Hotsilog", 60, 100),
        ("Chicksilog", 99, 100),
        ("Porksilog", 99, 100),
        ("Sisig Silog", 99, 100),

        ("Sizzling Sisig (Rice Meal)", 109, 100),
        ("Sizzling Tofu (Rice Meal)", 109, 100),
        ("Sizzling Liempo (Rice Meal)", 109, 100),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO products (name, price, stock) VALUES (?, ?, ?)",
        products
    )

    # INGREDIENT INVENTORY
    ingredients = [

        ("Pork", 5000, "grams"),
        ("Liempo", 5000, "grams"),
        ("Chicken Fillet", 5000, "grams"),
        ("Tofu", 2000, "grams"),
        ("Beef", 2000, "grams"),
        ("Potato Fries", 5000, "grams"),

        ("Egg", 200, "pcs"),
        ("Green Chili", 50, "pcs"),
        ("Red Chili", 50, "pcs"),
        ("Onion", 100, "pcs"),
        ("Garlic", 100, "pcs"),
        ("Tomato", 50, "pcs"),
        ("Cucumber", 50, "pcs"),

        ("Butter", 500, "grams"),
        ("Seasoning", 500, "tsp"),
        ("Oyster Sauce", 500, "tsp"),

        ("All Purpose Flour", 2000, "grams"),
        ("Bread Crumbs", 2000, "grams"),

        ("Cooking Oil", 1500, "ml"),

        ("Cheese", 100, "slices"),
        ("Ham", 100, "slices"),
        ("Crab Stick", 100, "slices")
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO ingredients (name, stock, unit) VALUES (?, ?, ?)",
        ingredients
    )

    # RECIPES (ingredient usage per menu item)
    recipes = [

        ("Sizzling Sisig", "Pork", 100, "grams"),
        ("Sizzling Sisig", "Green Chili", 1, "pcs"),
        ("Sizzling Sisig", "Egg", 1, "pcs"),
        ("Sizzling Sisig", "Onion", 0.25, "pcs"),
        ("Sizzling Sisig", "Butter", 5, "grams"),
        ("Sizzling Sisig", "Seasoning", 0.5, "tsp"),

        ("Sizzling Liempo", "Liempo", 100, "grams"),
        ("Sizzling Liempo", "Seasoning", 0.5, "tsp"),
        ("Sizzling Liempo", "Oyster Sauce", 0.5, "tsp"),

        ("Sizzling Tofu", "Tofu", 100, "grams"),
        ("Sizzling Tofu", "Red Chili", 1, "pcs"),
        ("Sizzling Tofu", "Onion", 0.25, "pcs"),

        ("Nachos", "Beef", 100, "grams"),
        ("Nachos", "Cucumber", 0.25, "pcs"),
        ("Nachos", "Tomato", 1, "pcs"),

        ("Porksilog", "Pork", 125, "grams"),
        ("Porksilog", "Bread Crumbs", 10, "grams"),
        ("Porksilog", "All Purpose Flour", 10, "grams"),
        ("Porksilog", "Egg", 1, "pcs"),

        ("Chicken Tenders - Cheese", "Chicken Fillet", 150, "grams"),
        ("Chicken Tenders - Cheese", "Bread Crumbs", 10, "grams"),
        ("Chicken Tenders - Cheese", "All Purpose Flour", 10, "grams"),
        ("Chicken Tenders - Cheese", "Egg", 1, "pcs"),

        ("Fries - Cheese", "Potato Fries", 250, "grams"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
        recipes
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    insert_default_data()