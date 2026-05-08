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

    # Ensure missing columns exist for backward compatibility
    cursor.execute("PRAGMA table_info(products)")
    columns = [row[1] for row in cursor.fetchall()]

    if "category" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'unknown'")
        cursor.execute("UPDATE products SET category = 'unknown' WHERE category IS NULL")

    if "stock" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0")

    # PRODUCT ARCHIVE TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER,
        category TEXT,
        archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # INGREDIENTS ARCHIVE TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        stock REAL,
        unit TEXT,
        archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    # TRANSACTION ARCHIVE TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaction_archive (
        id INTEGER PRIMARY KEY,
        total REAL,
        payment REAL,
        change REAL,
        date TIMESTAMP,
        archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # TRANSACTION ITEMS ARCHIVE TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaction_items_archive (
        id INTEGER PRIMARY KEY,
        transaction_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        subtotal REAL
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
        ("inventory_staff", "1234", "inventory_staff"),
        ("admin", "1234", "admin")
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        users
    )

    # PRODUCTS (Complete menu with stock and categories)
    products = [
        # Snacks
        ("Nachos", 80, 100, "snacks"),
        ("Fries - Cheese", 50, 100, "snacks"),
        ("Fries - Barbeque", 50, 100, "snacks"),
        ("Fries - Sour and Cream", 50, 100, "snacks"),
        ("Takoyaki - Cheese (5pcs)", 45, 100, "snacks"),
        ("Takoyaki - Ham and Cheese (5pcs)", 50, 100, "snacks"),
        ("Takoyaki - Crab (5pcs)", 50, 100, "snacks"),
        ("Takoyaki - Overload (7pcs)", 80, 100, "snacks"),
        ("Shawarma Rice", 80, 100, "snacks"),

        # Rice Meals
        ("Chicken Tenders", 70, 100, "meals"),    
        ("Sisig Silog", 109, 100, "meals"),
        ("Chicken silog", 99, 100, "meals"),
        ("Sizzling Sisig (Rice Meal)", 109, 100, "meals"),
        ("Sizzling Tofu (Rice Meal)", 109, 100, "meals"),
        ("Sizzling Liempo (Rice Meal)", 109, 100, "meals"),

        # Bundle Meals   
        ("Sizzling Sisig", 199, 100, "meals"),
        ("Sizzling Tofu", 199, 100, "meals"),
        ("Sizzling Liempo", 199, 100, "meals"),
        ("Sisig and Liempo", 199, 100, "meals"),
        ("Sisig and Tofu", 199, 100, "meals"),
        ("Sizzling Liempo and Tofu", 199, 100, "meals"),
        
        # Beverages
        ("Red Horse 1 Litro", 150, 100, "alcohol"),
        ("Alfonso Light", 350, 100, "alcohol"),
        ("Gin Bilog", 85, 100, "alcohol"),
        ("Gin Kwatro", 180, 100, "alcohol"),
        ("Pale Pilsen", 150, 100, "alcohol"),

        # Milk Tea
        ("Chocolate Milk Tea", 39, 100, "drinks"),
        ("Chocolate Milk Tea 1 liter", 89, 100, "drinks"),
        ("Okinawa Milk Tea", 39, 100, "drinks"),
        ("Okinawa Milk Tea 1 liter", 89, 100, "drinks"),
        ("Dark Chocolate Milk Tea", 39, 100, "drinks"),
        ("Dark Chocolate Milk Tea 1 liter", 89, 100, "drinks"),
        ("Taro Milk Tea", 39, 100, "drinks"),
        ("Taro Milk Tea 1 liter", 89, 100, "drinks"),
        ("Red Velvet Milk Tea", 39, 100, "drinks"),
        ("Red Velvet Milk Tea 1 liter", 89, 100, "drinks"),
        ("Matcha Milk Tea", 39, 100, "drinks"),
        ("Matcha Milk Tea 1 liter", 89, 100, "drinks"),
        ("Wintermelon Milk Tea", 39, 100, "drinks"),
        ("Wintermelon Milk Tea 1 liter", 89, 100, "drinks"),
        ("Cookies & Cream Milk Tea", 39, 100, "drinks"),
        ("Cookies & Cream Milk Tea 1 liter", 89, 100, "drinks"),
        ("White Bunny Milk Tea", 39, 100, "drinks"),
        ("White Bunny Milk Tea 1 liter", 89, 100, "drinks"),
        ("Mango Cheesecake Milk Tea", 39, 100, "drinks"),
        ("Mango Cheesecake Milk Tea 1 liter", 89, 100, "drinks"),

        # Fruit Tea
        ("Blueberry Fruit Tea", 39, 100, "drinks"),
        ("Blueberry Fruit Tea 1 liter", 89, 100, "drinks"),
        ("Strawberry Fruit Tea", 39, 100, "drinks"),
        ("Strawberry Fruit Tea 1 liter", 89, 100, "drinks"),
        ("Green Apple Fruit Tea", 39, 100, "drinks"),
        ("Green Apple Fruit Tea 1 liter", 89, 100, "drinks"),
        ("Four Seasons Fruit Tea", 39, 100, "drinks"),
        ("Four Seasons Fruit Tea 1 liter", 89, 100, "drinks"),
        ("Lychee Fruit Tea", 39, 100, "drinks"),
        ("Lychee Fruit Tea 1 liter", 89, 100, "drinks"),
        ("Blue Lemonade Fruit Tea", 39, 100, "drinks"),
        ("Blue Lemonade Fruit Tea 1 liter", 89, 100, "drinks"),

        # Fruit Soda
        ("Blueberry Fruit Soda", 39, 100, "drinks"),
        ("Blueberry Fruit Soda 1 liter", 89, 100, "drinks"),
        ("Strawberry Fruit Soda", 39, 100, "drinks"),
        ("Strawberry Fruit Soda 1 liter", 89, 100, "drinks"),
        ("Green Apple Fruit Soda", 39, 100, "drinks"),
        ("Green Apple Fruit Soda 1 liter", 89, 100, "drinks"),
        ("Four Seasons Fruit Soda", 39, 100, "drinks"),
        ("Four Seasons Fruit Soda 1 liter", 89, 100, "drinks"),
        ("Lychee Fruit Soda", 39, 100, "drinks"),
        ("Lychee Fruit Soda 1 liter", 89, 100, "drinks"),
        ("Blue Lemonade Fruit Soda", 39, 100, "drinks"),
        ("Blue Lemonade Fruit Soda 1 liter", 89, 100, "drinks"),

        # Add ons
        ("Pearl", 10, 100, "drinks"),
        ("Nata De Coco", 10, 100, "drinks")      
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
        products
    )

    # INGREDIENT INVENTORY (Complete ingredient list)
    recipes = [

# ================= SNACKS =================

    ("Nachos", "Beef", 100, "grams"),
    ("Nachos", "Tomato", 1, "pcs"),
    ("Nachos", "Onion", 0.25, "pcs"),
    ("Nachos", "Cheese", 2, "slices"),

    ("Fries - Cheese", "Potato Fries", 150, "grams"),
    ("Fries - Cheese", "Cheese", 2, "slices"),
    ("Fries - Cheese", "Cooking Oil", 20, "ml"),

    ("Fries - Barbeque", "Potato Fries", 150, "grams"),
    ("Fries - Barbeque", "Seasoning", 1, "tsp"),
    ("Fries - Barbeque", "Cooking Oil", 20, "ml"),

    ("Fries - Sour and Cream", "Potato Fries", 150, "grams"),
    ("Fries - Sour and Cream", "Seasoning", 1, "tsp"),
    ("Fries - Sour and Cream", "Cooking Oil", 20, "ml"),

    ("Takoyaki - Cheese (5pcs)", "All Purpose Flour", 50, "grams"),
    ("Takoyaki - Cheese (5pcs)", "Egg", 1, "pcs"),
    ("Takoyaki - Cheese (5pcs)", "Cheese", 2, "slices"),
    ("Takoyaki - Cheese (5pcs)", "Cooking Oil", 10, "ml"),
    ("Takoyaki - Cheese (5pcs)", "Onion", 0.25, "pcs"),

    ("Takoyaki - Ham and Cheese (5pcs)", "All Purpose Flour", 50, "grams"),
    ("Takoyaki - Ham and Cheese (5pcs)", "Egg", 1, "pcs"),
    ("Takoyaki - Ham and Cheese (5pcs)", "Cheese", 2, "slices"),
    ("Takoyaki - Ham and Cheese (5pcs)", "Ham", 2, "slices"),
    ("Takoyaki - Ham and Cheese (5pcs)", "Cooking Oil", 10, "ml"),

    ("Takoyaki - Crab (5pcs)", "All Purpose Flour", 50, "grams"),
    ("Takoyaki - Crab (5pcs)", "Egg", 1, "pcs"),
    ("Takoyaki - Crab (5pcs)", "Crab Stick", 2, "slices"),
    ("Takoyaki - Crab (5pcs)", "Onion", 0.25, "pcs"),
    ("Takoyaki - Crab (5pcs)", "Cooking Oil", 10, "ml"),

    ("Takoyaki - Overload (7pcs)", "All Purpose Flour", 60, "grams"),
    ("Takoyaki - Overload (7pcs)", "Egg", 1, "pcs"),
    ("Takoyaki - Overload (7pcs)", "Cheese", 2, "slices"),
    ("Takoyaki - Overload (7pcs)", "Ham", 2, "slices"),
    ("Takoyaki - Overload (7pcs)", "Crab Stick", 2, "slices"),

    ("Shawarma Rice", "Chicken Fillet", 120, "grams"),
    ("Shawarma Rice", "Cucumber", 0.25, "pcs"),
    ("Shawarma Rice", "Onion", 0.25, "pcs"),
    ("Shawarma Rice", "Garlic", 0.25, "pcs"),

    # ================= MEALS =================

    ("Chicken Tenders", "Chicken Fillet", 150, "grams"),
    ("Chicken Tenders", "All Purpose Flour", 10, "grams"),
    ("Chicken Tenders", "Bread Crumbs", 10, "grams"),
    ("Chicken Tenders", "Egg", 1, "pcs"),

    ("Sisig Silog", "Pork", 100, "grams"),
    ("Sisig Silog", "Egg", 1, "pcs"),
    ("Sisig Silog", "Onion", 0.25, "pcs"),
    ("Sisig Silog", "Green Chili", 1, "pcs"),

    ("Chicken silog", "Chicken Fillet", 120, "grams"),
    ("Chicken silog", "Egg", 1, "pcs"),
    ("Chicken silog", "Garlic", 0.25, "pcs"),
    ("Chicken silog", "Cooking Oil", 10, "ml"),

    ("Sizzling Sisig (Rice Meal)", "Pork", 100, "grams"),
    ("Sizzling Sisig (Rice Meal)", "Egg", 1, "pcs"),
    ("Sizzling Sisig (Rice Meal)", "Onion", 0.25, "pcs"),
    ("Sizzling Sisig (Rice Meal)", "Seasoning", 0.5, "tsp"),

    ("Sizzling Tofu (Rice Meal)", "Tofu", 100, "grams"),
    ("Sizzling Tofu (Rice Meal)", "Red Chili", 1, "pcs"),
    ("Sizzling Tofu (Rice Meal)", "Oyster Sauce", 0.5, "tsp"),

    ("Sizzling Liempo (Rice Meal)", "Liempo", 100, "grams"),
    ("Sizzling Liempo (Rice Meal)", "Garlic", 0.25, "pcs"),
    ("Sizzling Liempo (Rice Meal)", "Seasoning", 0.5, "tsp"),

    # ================= BUNDLES =================

    ("Sizzling Sisig", "Pork", 120, "grams"),
    ("Sizzling Sisig", "Onion", 0.25, "pcs"),
    ("Sizzling Sisig", "Egg", 1, "pcs"),
    ("Sizzling Sisig", "Green Chili", 1, "pcs"),

    ("Sizzling Tofu", "Tofu", 120, "grams"),
    ("Sizzling Tofu", "Red Chili", 1, "pcs"),
    ("Sizzling Tofu", "Oyster Sauce", 0.5, "tsp"),

    ("Sizzling Liempo", "Liempo", 120, "grams"),
    ("Sizzling Liempo", "Garlic", 0.25, "pcs"),
    ("Sizzling Liempo", "Seasoning", 0.5, "tsp"),

    ("Sisig and Liempo", "Pork", 80, "grams"),
    ("Sisig and Liempo", "Liempo", 80, "grams"),
    ("Sisig and Liempo", "Onion", 0.25, "pcs"),

    ("Sisig and Tofu", "Pork", 80, "grams"),
    ("Sisig and Tofu", "Tofu", 80, "grams"),
    ("Sisig and Tofu", "Onion", 0.25, "pcs"),

    ("Sizzling Liempo and Tofu", "Liempo", 80, "grams"),
    ("Sizzling Liempo and Tofu", "Tofu", 80, "grams"),
    ("Sizzling Liempo and Tofu", "Garlic", 0.25, "pcs"),

    # ================= DRINKS (placeholder minimal) =================

    ("Chocolate Milk Tea", "Seasoning", 1, "tsp"),
    ("Okinawa Milk Tea", "Seasoning", 1, "tsp"),
    ("Taro Milk Tea", "Seasoning", 1, "tsp"),
    ("Matcha Milk Tea", "Seasoning", 1, "tsp"),
    ("Wintermelon Milk Tea", "Seasoning", 1, "tsp"),

    ("Blueberry Fruit Tea", "Seasoning", 1, "tsp"),
    ("Strawberry Fruit Tea", "Seasoning", 1, "tsp"),
    ("Green Apple Fruit Tea", "Seasoning", 1, "tsp"),

    ("Blueberry Fruit Soda", "Seasoning", 1, "tsp"),
    ("Strawberry Fruit Soda", "Seasoning", 1, "tsp"),
    ("Green Apple Fruit Soda", "Seasoning", 1, "tsp"),

    ("Pearl", "Seasoning", 1, "tsp"),
    ("Nata De Coco", "Seasoning", 1, "tsp"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
        recipes
    )

    conn.commit()
    conn.close()


def archive_product(product_id):
    """Archive a product by moving it to archive table"""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Get product data
    cursor.execute("SELECT name, price, stock, category FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    
    if product:
        # Insert into archive
        cursor.execute(
            "INSERT INTO product_archive (name, price, stock, category) VALUES (?, ?, ?, ?)",
            product
        )
        # Delete from main table
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
    
    conn.close()


def archive_ingredient(ingredient_id):
    """Archive an ingredient by moving it to archive table"""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Get ingredient data
    cursor.execute("SELECT name, stock, unit FROM ingredients WHERE id = ?", (ingredient_id,))
    ingredient = cursor.fetchone()
    
    if ingredient:
        # Insert into archive
        cursor.execute(
            "INSERT INTO ingredients_archive (name, stock, unit) VALUES (?, ?, ?)",
            ingredient
        )
        # Delete from main table
        cursor.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,))
        conn.commit()
    
    conn.close()


def get_archived_products():
    """Get all archived products"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product_archive ORDER BY archived_date DESC")
    products = cursor.fetchall()
    conn.close()
    return products


def get_archived_ingredients():
    """Get all archived ingredients"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ingredients_archive ORDER BY archived_date DESC")
    ingredients = cursor.fetchall()
    conn.close()
    return ingredients


def prompt_success():
    print("\n" + "="*50)
    print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("\nDatabase Summary:")

if __name__ == "__main__":
    create_tables()
    insert_default_data()
    prompt_success()