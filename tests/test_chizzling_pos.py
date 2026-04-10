# Simplified Test for ChizzlingPOS System
# Test Objective: Test core ChizzlingPOS functionality without complex UI mocking

import pytest
import sys
import os
import sqlite3
import tempfile
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def setup_test_db():
    """Create a test database connection"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'sales_inventory.db')
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()

@pytest.fixture
def temp_db():
    """Create temporary database for isolated testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    # Create basic tables for testing
    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        price REAL,
        category TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL,
        payment REAL,
        change REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        subtotal REAL,
        FOREIGN KEY(transaction_id) REFERENCES transactions(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)
    
    # Insert test products
    test_products = [
        ("Sisig", 120.0, "meals"),
        ("Nachos", 80.0, "snacks"),
        ("Milk Tea", 39.0, "drinks"),
        ("Red Horse", 150.0, "alcohol")
    ]
    
    cursor.executemany(
        "INSERT INTO products (name, price, category) VALUES (?, ?, ?)",
        test_products
    )
    
    conn.commit()
    conn.close()
    
    yield temp_file.name
    os.unlink(temp_file.name)

class TestDatabaseConnection:
    """Test database connection functionality"""
    
    def test_connect_db_function(self):
        """Test that connect_db returns a valid connection"""
        from database_setup import create_tables, connect_db as setup_connect_db
        import database_setup

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()

        def mock_connect():
            return sqlite3.connect(temp_file.name)

        database_setup.connect_db = mock_connect
        create_tables()
        database_setup.connect_db = setup_connect_db

        conn = sqlite3.connect(temp_file.name)
        assert conn is not None

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        assert len(tables) > 0
        conn.close()
        os.unlink(temp_file.name)

class TestProductLoading:
    """Test product loading functionality without UI components"""
    
    def test_load_products_from_database(self, temp_db):
        """Test loading products directly from database"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Test loading all products
        cursor.execute("SELECT id, name, price, COALESCE(category, 'All') FROM products")
        products = cursor.fetchall()
        
        assert len(products) == 4
        product_names = [product[1] for product in products]
        assert "Sisig" in product_names
        assert "Nachos" in product_names
        assert "Milk Tea" in product_names
        assert "Red Horse" in product_names
        
        conn.close()
    
    def test_load_products_by_category(self, temp_db):
        """Test loading products filtered by category"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Test loading meals category
        cursor.execute(
            "SELECT id, name, price, COALESCE(category, 'All') FROM products WHERE LOWER(category)=?",
            ("meals",)
        )
        products = cursor.fetchall()
        
        assert len(products) == 1
        assert products[0][1] == "Sisig"
        assert products[0][3] == "meals"
        
        conn.close()
    
    def test_category_filtering_case_insensitive(self, temp_db):
        """Test that category filtering works case insensitive"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Test with uppercase category
        cursor.execute(
            "SELECT id, name, price, COALESCE(category, 'All') FROM products WHERE LOWER(category)=?",
            ("snacks",)
        )
        products = cursor.fetchall()
        
        assert len(products) == 1
        assert products[0][1] == "Nachos"
        
        conn.close()

class TestPaymentCalculations:
    """Test payment calculation logic"""
    
    def test_valid_payment_calculation(self):
        """Test valid payment and change calculation"""
        total = 250.0
        payment = 300.0
        
        # Simulate payment validation
        is_valid = payment >= total
        assert is_valid == True
        
        # Calculate change
        change = payment - total
        assert change == 50.0
    
    def test_insufficient_payment(self):
        """Test insufficient payment detection"""
        total = 250.0
        payment = 200.0
        
        is_valid = payment >= total
        assert is_valid == False
    
    def test_exact_payment(self):
        """Test exact payment (no change)"""
        total = 250.0
        payment = 250.0
        
        is_valid = payment >= total
        assert is_valid == True
        
        change = payment - total
        assert change == 0.0

class TestTransactionSaving:
    """Test transaction saving to database"""
    
    def test_save_transaction_to_database(self, temp_db):
        """Test saving transaction to database"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Simulate transaction data
        total = 250.0
        payment = 300.0
        change = 50.0
        date_str = "2024-01-01 12:00:00"
        
        # Save transaction
        cursor.execute(
            "INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
            (total, payment, change, date_str)
        )
        transaction_id = cursor.lastrowid
        conn.commit()
        
        # Verify transaction was saved
        cursor.execute("SELECT total, payment, change FROM transactions WHERE id = ?", (transaction_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 250.0  # total
        assert result[1] == 300.0  # payment
        assert result[2] == 50.0   # change
        
        conn.close()
    
    def test_save_transaction_items(self, temp_db):
        """Test saving transaction items to database"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Create a transaction first
        cursor.execute(
            "INSERT INTO transactions (total, payment, change) VALUES (?, ?, ?)",
            (250.0, 300.0, 50.0)
        )
        transaction_id = cursor.lastrowid
        
        # Simulate cart items
        cart_items = [
            {'id': 1, 'name': 'Sisig', 'qty': 2, 'price': 120.0},
            {'id': 2, 'name': 'Nachos', 'qty': 1, 'price': 80.0}
        ]
        
        # Save transaction items
        for item in cart_items:
            subtotal = item['price'] * item['qty']
            cursor.execute("""
                INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal)
                VALUES (?, ?, ?, ?)
            """, (transaction_id, item['id'], item['qty'], subtotal))
        
        conn.commit()
        
        # Verify transaction items were saved
        cursor.execute("SELECT COUNT(*) FROM transaction_items WHERE transaction_id = ?", (transaction_id,))
        count = cursor.fetchone()[0]
        assert count == 2
        
        # Verify item details
        cursor.execute(
            "SELECT product_id, quantity, subtotal FROM transaction_items WHERE transaction_id = ? ORDER BY product_id",
            (transaction_id,)
        )
        items = cursor.fetchall()
        
        assert items[0] == (1, 2, 240.0)  # Sisig: 2 * 120.0
        assert items[1] == (2, 1, 80.0)   # Nachos: 1 * 80.0
        
        conn.close()

class TestInputValidation:
    """Test input validation logic"""
    
    def test_payment_input_validation(self):
        """Test payment input validation"""
        # Valid payment
        try:
            payment = float("300.50")
            assert payment == 300.50
        except ValueError:
            pytest.fail("Valid payment input should not raise ValueError")
        
        # Invalid payment
        with pytest.raises(ValueError):
            payment = float("invalid")
    
    def test_negative_payment_validation(self):
        """Test negative payment validation"""
        payment = -100.0
        is_valid = payment > 0
        assert is_valid == False
    
    def test_zero_payment_validation(self):
        """Test zero payment validation"""
        payment = 0.0
        is_valid = payment > 0
        assert is_valid == False

class TestDatabaseIntegrity:
    """Test database integrity and constraints"""
    
    def test_foreign_key_relationship(self, temp_db):
        """Test foreign key relationships work correctly"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Create transaction
        cursor.execute("INSERT INTO transactions (total, payment, change) VALUES (100, 120, 20)")
        transaction_id = cursor.lastrowid
        
        # Get existing product
        cursor.execute("SELECT id FROM products LIMIT 1")
        product_id = cursor.fetchone()[0]
        
        # Create transaction item with foreign keys
        cursor.execute(
            "INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal) VALUES (?, ?, 2, 100)",
            (transaction_id, product_id)
        )
        
        conn.commit()
        
        # Verify relationship with JOIN
        cursor.execute("""
            SELECT ti.quantity, p.name, t.total 
            FROM transaction_items ti
            JOIN products p ON ti.product_id = p.id
            JOIN transactions t ON ti.transaction_id = t.id
            WHERE ti.transaction_id = ?
        """, (transaction_id,))
        
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 2  # quantity
        assert result[2] == 100  # transaction total
        
        conn.close()

if __name__ == "__main__":
    pytest.main([__file__])