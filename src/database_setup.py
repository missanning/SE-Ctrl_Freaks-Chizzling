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
    ingredients = [
        # Proteins
        ("Pork", 5000, "grams"),
        ("Liempo", 5000, "grams"),
        ("Chicken Fillet", 5000, "grams"),
        ("Tofu", 2000, "grams"),
        ("Beef", 2000, "grams"),
        ("Potato Fries", 5000, "grams"),

        # Vegetables
        ("Egg", 200, "pcs"),
        ("Green Chili", 50, "pcs"),
        ("Red Chili", 50, "pcs"),
        ("Onion", 100, "pcs"),
        ("Garlic", 100, "pcs"),
        ("Tomato", 50, "pcs"),
        ("Cucumber", 50, "pcs"),

        # Seasonings & Sauces
        ("Butter", 500, "grams"),
        ("Seasoning", 500, "tsp"),
        ("Oyster Sauce", 500, "tsp"),

        # Flour & Breading
        ("All Purpose Flour", 2000, "grams"),
        ("Bread Crumbs", 2000, "grams"),

        # Cooking Oil
        ("Cooking Oil", 1500, "ml"),

        # Dairy & Processed
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

    # Sizzling Sisig (5 ingredients)
    ("Sizzling Sisig", "Pork", 100, "grams"),
    ("Sizzling Sisig", "Onion", 0.25, "pcs"),
    ("Sizzling Sisig", "Egg", 1, "pcs"),
    ("Sizzling Sisig", "Green Chili", 1, "pcs"),
    ("Sizzling Sisig", "Seasoning", 0.5, "tsp"),

    # Sizzling Liempo (4 ingredients)
    ("Sizzling Liempo", "Liempo", 100, "grams"),
    ("Sizzling Liempo", "Garlic", 0.5, "pcs"),
    ("Sizzling Liempo", "Oyster Sauce", 0.5, "tsp"),
    ("Sizzling Liempo", "Seasoning", 0.5, "tsp"),

    # Sizzling Tofu (4 ingredients)
    ("Sizzling Tofu", "Tofu", 100, "grams"),
    ("Sizzling Tofu", "Onion", 0.25, "pcs"),
    ("Sizzling Tofu", "Red Chili", 1, "pcs"),
    ("Sizzling Tofu", "Oyster Sauce", 0.5, "tsp"),

    # Chicken Tenders (4 ingredients) — FIXED NAME
    ("Chicken Tenders", "Chicken Fillet", 150, "grams"),
    ("Chicken Tenders", "All Purpose Flour", 10, "grams"),
    ("Chicken Tenders", "Bread Crumbs", 10, "grams"),
    ("Chicken Tenders", "Egg", 1, "pcs"),

    # Nachos (4 ingredients)
    ("Nachos", "Beef", 100, "grams"),
    ("Nachos", "Tomato", 1, "pcs"),
    ("Nachos", "Onion", 0.25, "pcs"),
    ("Nachos", "Cheese", 2, "slices"),

    # Takoyaki - Cheese (5pcs)
    ("Takoyaki - Cheese (5pcs)", "All Purpose Flour", 50, "grams"),
    ("Takoyaki - Cheese (5pcs)", "Egg", 1, "pcs"),
    ("Takoyaki - Cheese (5pcs)", "Cheese", 2, "slices"),
    ("Takoyaki - Cheese (5pcs)", "Cooking Oil", 10, "ml"),
    ("Takoyaki - Cheese (5pcs)", "Onion", 0.25, "pcs"),

    # Takoyaki - Ham and Cheese (5pcs)
    ("Takoyaki - Ham and Cheese (5pcs)", "All Purpose Flour", 50, "grams"),
    ("Takoyaki - Ham and Cheese (5pcs)", "Egg", 1, "pcs"),
    ("Takoyaki - Ham and Cheese (5pcs)", "Cheese", 2, "slices"),
    ("Takoyaki - Ham and Cheese (5pcs)", "Ham", 2, "slices"),
    ("Takoyaki - Ham and Cheese (5pcs)", "Cooking Oil", 10, "ml"),

    # Takoyaki - Crab (5pcs)
    ("Takoyaki - Crab (5pcs)", "All Purpose Flour", 50, "grams"),
    ("Takoyaki - Crab (5pcs)", "Egg", 1, "pcs"),
    ("Takoyaki - Crab (5pcs)", "Crab Stick", 2, "slices"),
    ("Takoyaki - Crab (5pcs)", "Onion", 0.25, "pcs"),
    ("Takoyaki - Crab (5pcs)", "Cooking Oil", 10, "ml"),

    # Takoyaki - Overload (7pcs)
    ("Takoyaki - Overload (7pcs)", "All Purpose Flour", 60, "grams"),
    ("Takoyaki - Overload (7pcs)", "Egg", 1, "pcs"),
    ("Takoyaki - Overload (7pcs)", "Cheese", 2, "slices"),
    ("Takoyaki - Overload (7pcs)", "Ham", 2, "slices"),
    ("Takoyaki - Overload (7pcs)", "Crab Stick", 2, "slices"),
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