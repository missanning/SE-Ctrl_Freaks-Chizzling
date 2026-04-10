# Test for US-13: Database Setup and Initialization
# Test Objective: Ensure that all necessary database tables are successfully created 
# and that default records for users, products, ingredients, and recipes are properly inserted without errors.

import pytest
import sys
import os
import sqlite3
import tempfile
import shutil

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database_setup import create_tables, insert_default_data, connect_db

@pytest.fixture
def temp_db():
    """Create temporary database for isolated testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)

@pytest.fixture
def temp_db_with_tables(temp_db):
    """Create temporary database with tables already created"""
    # Temporarily replace the database path in database_setup
    original_connect = connect_db
    
    def mock_connect():
        return sqlite3.connect(temp_db)
    
    # Monkey patch the connect_db function
    import database_setup
    database_setup.connect_db = mock_connect
    
    # Create tables
    create_tables()
    
    yield temp_db
    
    # Restore original function
    database_setup.connect_db = original_connect

class TestDatabaseTableCreation:
    """Test database table creation functionality"""
    
    def test_all_required_tables_created(self, temp_db_with_tables):
        """Test that all 6 required tables are created successfully"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Verify all required tables exist
        required_tables = [
            'users', 
            'products', 
            'transactions', 
            'transaction_items', 
            'ingredients', 
            'recipe_ingredients'
        ]
        
        for table in required_tables:
            assert table in tables, f"Required table '{table}' was not created"
        
        conn.close()
    
    def test_users_table_structure(self, temp_db_with_tables):
        """Test users table has correct column structure"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()
        
        # Extract column names and types
        columns = {row[1]: row[2] for row in columns_info}
        
        # Verify required columns exist with correct types
        expected_columns = {
            'id': 'INTEGER',
            'username': 'TEXT',
            'password': 'TEXT',
            'role': 'TEXT'
        }
        
        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column '{col_name}' missing from users table"
            assert columns[col_name] == col_type, f"Column '{col_name}' has wrong type: expected {col_type}, got {columns[col_name]}"
        
        conn.close()
    
    def test_products_table_structure(self, temp_db_with_tables):
        """Test products table has correct column structure"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(products)")
        columns_info = cursor.fetchall()
        columns = {row[1]: row[2] for row in columns_info}
        
        expected_columns = {
            'id': 'INTEGER',
            'name': 'TEXT',
            'price': 'REAL',
            'category': 'TEXT'
        }
        
        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column '{col_name}' missing from products table"
            assert columns[col_name] == col_type, f"Column '{col_name}' has wrong type"
        
        conn.close()
    
    def test_transactions_table_structure(self, temp_db_with_tables):
        """Test transactions table has correct column structure"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(transactions)")
        columns_info = cursor.fetchall()
        columns = {row[1]: row[2] for row in columns_info}
        
        expected_columns = {
            'id': 'INTEGER',
            'total': 'REAL',
            'payment': 'REAL',
            'change': 'REAL',
            'date': 'TIMESTAMP'
        }
        
        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column '{col_name}' missing from transactions table"
        
        conn.close()
    
    def test_transaction_items_table_structure(self, temp_db_with_tables):
        """Test transaction_items table has correct structure with foreign keys"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(transaction_items)")
        columns_info = cursor.fetchall()
        columns = {row[1]: row[2] for row in columns_info}
        
        expected_columns = {
            'id': 'INTEGER',
            'transaction_id': 'INTEGER',
            'product_id': 'INTEGER',
            'quantity': 'INTEGER',
            'subtotal': 'REAL'
        }
        
        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column '{col_name}' missing from transaction_items table"
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_key_list(transaction_items)")
        foreign_keys = cursor.fetchall()
        
        fk_tables = [fk[2] for fk in foreign_keys]
        assert 'transactions' in fk_tables, "Foreign key to transactions table missing"
        assert 'products' in fk_tables, "Foreign key to products table missing"
        
        conn.close()
    
    def test_ingredients_table_structure(self, temp_db_with_tables):
        """Test ingredients table has correct column structure"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(ingredients)")
        columns_info = cursor.fetchall()
        columns = {row[1]: row[2] for row in columns_info}
        
        expected_columns = {
            'id': 'INTEGER',
            'name': 'TEXT',
            'stock': 'REAL',
            'unit': 'TEXT'
        }
        
        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column '{col_name}' missing from ingredients table"
        
        conn.close()
    
    def test_recipe_ingredients_table_structure(self, temp_db_with_tables):
        """Test recipe_ingredients table has correct column structure"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(recipe_ingredients)")
        columns_info = cursor.fetchall()
        columns = {row[1]: row[2] for row in columns_info}
        
        expected_columns = {
            'id': 'INTEGER',
            'product_name': 'TEXT',
            'ingredient_name': 'TEXT',
            'quantity': 'REAL',
            'unit': 'TEXT'
        }
        
        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column '{col_name}' missing from recipe_ingredients table"
        
        conn.close()

class TestDefaultDataInsertion:
    """Test default data insertion functionality"""
    
    def test_default_users_inserted(self, temp_db_with_tables):
        """Test that default users are properly inserted"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        # Temporarily replace connect_db for insert_default_data
        original_connect = connect_db
        
        def mock_connect():
            return sqlite3.connect(temp_db_with_tables)
        
        import database_setup
        database_setup.connect_db = mock_connect
        
        # Insert default data
        insert_default_data()
        
        # Verify default users exist
        cursor.execute("SELECT username, password, role FROM users ORDER BY username")
        users = cursor.fetchall()
        
        expected_users = [
            ('admin', '1234', 'owner'),
            ('cashier', '1234', 'cashier'),
            ('inventory_staff', '1234', 'inventory_staff')
        ]
        
        assert len(users) == 3, f"Expected 3 default users, got {len(users)}"
        
        for expected_user in expected_users:
            assert expected_user in users, f"Default user {expected_user[0]} not found or incorrect"
        
        # Restore original function
        database_setup.connect_db = original_connect
        conn.close()
    
    def test_default_products_inserted_with_categories(self, temp_db_with_tables):
        """Test that default products are inserted with correct categories"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        # Mock connect_db for insert_default_data
        original_connect = connect_db
        
        def mock_connect():
            return sqlite3.connect(temp_db_with_tables)
        
        import database_setup
        database_setup.connect_db = mock_connect
        
        insert_default_data()
        
        # Verify products exist
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        assert product_count > 0, "No default products were inserted"
        
        # Verify all categories are represented
        cursor.execute("SELECT DISTINCT category FROM products")
        categories = [row[0] for row in cursor.fetchall()]
        
        expected_categories = ['snacks', 'meals', 'alcohol', 'drinks']
        for category in expected_categories:
            assert category in categories, f"Category '{category}' not found in products"
        
        # Verify specific products exist
        cursor.execute("SELECT name, price, category FROM products WHERE name IN ('Nachos', 'Sisig Silog', 'Red Horse 1 Litro')")
        sample_products = cursor.fetchall()
        
        assert len(sample_products) == 3, "Sample products not found"
        
        # Verify product details
        product_dict = {product[0]: (product[1], product[2]) for product in sample_products}
        
        assert 'Nachos' in product_dict, "Nachos product not found"
        assert product_dict['Nachos'][0] == 80, "Nachos price incorrect"
        assert product_dict['Nachos'][1] == 'snacks', "Nachos category incorrect"
        
        database_setup.connect_db = original_connect
        conn.close()
    
    def test_default_ingredients_inserted(self, temp_db_with_tables):
        """Test that default ingredients are properly inserted"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        # Mock connect_db
        original_connect = connect_db
        
        def mock_connect():
            return sqlite3.connect(temp_db_with_tables)
        
        import database_setup
        database_setup.connect_db = mock_connect
        
        insert_default_data()
        
        # Verify ingredients exist
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        ingredient_count = cursor.fetchone()[0]
        assert ingredient_count > 0, "No default ingredients were inserted"
        
        # Verify specific ingredients
        cursor.execute("SELECT name, stock, unit FROM ingredients WHERE name IN ('Pork', 'Egg', 'Cheese')")
        sample_ingredients = cursor.fetchall()
        
        assert len(sample_ingredients) == 3, "Sample ingredients not found"
        
        # Verify ingredient details
        ingredient_dict = {ing[0]: (ing[1], ing[2]) for ing in sample_ingredients}
        
        assert 'Pork' in ingredient_dict, "Pork ingredient not found"
        assert ingredient_dict['Pork'][0] == 5000, "Pork stock incorrect"
        assert ingredient_dict['Pork'][1] == 'grams', "Pork unit incorrect"
        
        database_setup.connect_db = original_connect
        conn.close()
    
    def test_default_recipes_inserted(self, temp_db_with_tables):
        """Test that default recipes are properly inserted"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        # Mock connect_db
        original_connect = connect_db
        
        def mock_connect():
            return sqlite3.connect(temp_db_with_tables)
        
        import database_setup
        database_setup.connect_db = mock_connect
        
        insert_default_data()
        
        # Verify recipes exist
        cursor.execute("SELECT COUNT(*) FROM recipe_ingredients")
        recipe_count = cursor.fetchone()[0]
        assert recipe_count > 0, "No default recipes were inserted"
        
        # Verify specific recipe
        cursor.execute("""
            SELECT product_name, ingredient_name, quantity, unit 
            FROM recipe_ingredients 
            WHERE product_name = 'Sizzling Sisig'
        """)
        sisig_recipe = cursor.fetchall()
        
        assert len(sisig_recipe) > 0, "Sizzling Sisig recipe not found"
        
        # Verify recipe contains expected ingredients
        recipe_ingredients = [recipe[1] for recipe in sisig_recipe]
        expected_ingredients = ['Pork', 'Green Chili', 'Egg', 'Onion', 'Butter', 'Seasoning']
        
        for ingredient in expected_ingredients:
            assert ingredient in recipe_ingredients, f"Ingredient '{ingredient}' not found in Sizzling Sisig recipe"
        
        database_setup.connect_db = original_connect
        conn.close()

class TestDatabaseIntegrity:
    """Test database integrity and error handling"""
    
    def test_duplicate_insertion_handling(self, temp_db_with_tables):
        """Test that duplicate insertions are handled properly (INSERT OR IGNORE)"""
        conn = sqlite3.connect(temp_db_with_tables)
        cursor = conn.cursor()
        
        # Mock connect_db
        original_connect = connect_db
        
        def mock_connect():
            return sqlite3.connect(temp_db_with_tables)
        
        import database_setup
        database_setup.connect_db = mock_connect
        
        # Insert default data twice
        insert_default_data()
        initial_user_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        
        insert_default_data()  # Second insertion
        final_user_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        
        # Count should remain the same (no duplicates)
        assert initial_user_count == final_user_count, "Duplicate users were inserted"
        
        database_setup.connect_db = original_connect
        conn.close()
    
    def test_category_column_migration(self, temp_db):
        """Test that category column is added to existing products table"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Create products table without category column (simulating old database)
        cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            price REAL
        )
        """)
        
        # Insert a test product
        cursor.execute("INSERT INTO products (name, price) VALUES ('Test Product', 50.0)")
        conn.commit()
        
        # Mock connect_db to use our temp database
        original_connect = connect_db
        
        def mock_connect():
            return sqlite3.connect(temp_db)
        
        import database_setup
        database_setup.connect_db = mock_connect
        
        # Run create_tables which should add category column
        create_tables()
        
        # Verify category column was added
        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]
        assert 'category' in columns, "Category column was not added to existing products table"
        
        # Verify existing product got default category
        cursor.execute("SELECT category FROM products WHERE name = 'Test Product'")
        category = cursor.fetchone()[0]
        assert category == 'unknown', "Existing product did not get default category"
        
        database_setup.connect_db = original_connect
        conn.close()
    
    def test_complete_database_initialization(self):
        """Test complete database initialization process using actual database"""
        # This test uses the real database to ensure everything works end-to-end
        conn = connect_db()
        cursor = conn.cursor()
        
        # Verify all tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'products', 'transactions', 'transaction_items', 'ingredients', 'recipe_ingredients']
        for table in required_tables:
            assert table in tables, f"Table '{table}' missing from initialized database"
        
        # Verify default data exists
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        assert user_count >= 3, "Insufficient default users in database"
        
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        assert product_count > 0, "No products in database"
        
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        ingredient_count = cursor.fetchone()[0]
        assert ingredient_count > 0, "No ingredients in database"
        
        cursor.execute("SELECT COUNT(*) FROM recipe_ingredients")
        recipe_count = cursor.fetchone()[0]
        assert recipe_count > 0, "No recipes in database"
        
        conn.close()

if __name__ == "__main__":
    pytest.main([__file__])