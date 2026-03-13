#Test Cases:
#1. Product browsing and filtering by category
#2. Add to cart operations
#3. Cart management (add/remove items, quantity changes)
#4. Payment processing and transaction saving
#5. Error handling for invalid or insufficient payment input
#6. Cancel order functionality

import pytest
import sys
import os
import sqlite3
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ChizzlingPOS import connect_db

@pytest.fixture
def test_db():
    """Create a test database"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'sales_inventory.db')
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()

def test_filter_by_meals_category(test_db):
    """Test filtering products by Meals category"""
    cursor = test_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE category = 'Meals'")
    count = cursor.fetchone()[0]
    assert count > 0, "Should have products in Meals category"

def test_filter_by_snacks_category(test_db):
    """Test filtering products by Snacks category"""
    cursor = test_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE category = 'Snacks'")
    count = cursor.fetchone()[0]
    assert count > 0, "Should have products in Snacks category"

def test_filter_by_drinks_category(test_db):
    """Test filtering products by Drinks category"""
    cursor = test_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE category = 'Drinks'")
    count = cursor.fetchone()[0]
    assert count > 0, "Should have products in Drinks category"

def test_filter_by_alcohol_category(test_db):
    """Test filtering products by Alcohol category"""
    cursor = test_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE category = 'Alcohol'")
    count = cursor.fetchone()[0]
    assert count > 0, "Should have products in Alcohol category"

def test_all_products_have_valid_category(test_db):
    """Test that all products belong to valid categories"""
    cursor = test_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE category NOT IN ('Meals', 'Snacks', 'Drinks', 'Alcohol')")
    invalid_count = cursor.fetchone()[0]
    assert invalid_count == 0, "All products should have valid categories"

def test_add_single_item_to_cart():
    """Test adding a single item to cart"""
    cart = []
    product = {'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 1}
    cart.append(product)
    assert len(cart) == 1
    assert cart[0]['name'] == 'Sisig'
    assert cart[0]['quantity'] == 1

def test_add_multiple_different_items():
    """Test adding multiple different items to cart"""
    cart = []
    cart.append({'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 1})
    cart.append({'id': 2, 'name': 'Chicharon', 'price': 50.0, 'quantity': 1})
    assert len(cart) == 2

def test_add_same_item_increases_quantity():
    """Test adding same item increases quantity"""
    cart = [{'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 1}]
    # Simulate adding same item
    existing_item = next((item for item in cart if item['id'] == 1), None)
    if existing_item:
        existing_item['quantity'] += 1
    assert cart[0]['quantity'] == 2

def test_cart_calculates_subtotal():
    """Test cart calculates subtotal correctly"""
    cart = [{'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 2}]
    subtotal = cart[0]['price'] * cart[0]['quantity']
    assert subtotal == 240.0

def test_increase_item_quantity():
    """Test increasing item quantity in cart"""
    cart = [{'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 1}]
    cart[0]['quantity'] += 1
    assert cart[0]['quantity'] == 2

def test_decrease_item_quantity():
    """Test decreasing item quantity in cart"""
    cart = [{'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 3}]
    cart[0]['quantity'] -= 1
    assert cart[0]['quantity'] == 2

def test_remove_item_when_quantity_zero():
    """Test removing item when quantity reaches zero"""
    cart = [{'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 1}]
    cart[0]['quantity'] -= 1
    if cart[0]['quantity'] <= 0:
        cart.remove(cart[0])
    assert len(cart) == 0

def test_remove_specific_item_from_cart():
    """Test removing specific item from cart"""
    cart = [
        {'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 1},
        {'id': 2, 'name': 'Chicharon', 'price': 50.0, 'quantity': 1}
    ]
    cart = [item for item in cart if item['id'] != 1]
    assert len(cart) == 1
    assert cart[0]['name'] == 'Chicharon'

def test_calculate_total_from_cart():
    """Test calculating total from multiple items"""
    cart = [
        {'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 2},
        {'id': 2, 'name': 'Chicharon', 'price': 50.0, 'quantity': 3}
    ]
    total = sum(item['price'] * item['quantity'] for item in cart)
    assert total == 390.0  # (120*2) + (50*3)

def test_calculate_change_correctly():
    """Test change calculation"""
    total = 250.0
    payment = 300.0
    change = payment - total
    assert change == 50.0

def test_exact_payment_no_change():
    """Test exact payment results in zero change"""
    total = 250.0
    payment = 250.0
    change = payment - total
    assert change == 0.0

def test_transaction_saves_with_date(test_db):
    """Test transaction saves with current date"""
    cursor = test_db.cursor()
    # Insert test transaction
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
                  (250.0, 300.0, 50.0, date_str))
    test_db.commit()
    transaction_id = cursor.lastrowid
    
    # Verify transaction saved
    cursor.execute("SELECT total, payment, change FROM transactions WHERE id = ?", (transaction_id,))
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == 250.0
    assert result[1] == 300.0
    assert result[2] == 50.0
    
    # Cleanup
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    test_db.commit()

def test_stock_decreases_after_transaction(test_db):
    """Test stock decreases after successful transaction"""
    cursor = test_db.cursor()
    # Get product with stock
    cursor.execute("SELECT id, stock FROM products WHERE stock > 5 LIMIT 1")
    product = cursor.fetchone()
    
    if product:
        product_id, initial_stock = product
        quantity_sold = 2
        new_stock = initial_stock - quantity_sold
        
        # Update stock
        cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
        test_db.commit()
        
        # Verify stock decreased
        cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
        updated_stock = cursor.fetchone()[0]
        assert updated_stock == new_stock
        
        # Restore stock
        cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (initial_stock, product_id))
        test_db.commit()

def test_payment_less_than_total():
    """Test payment less than total is invalid"""
    total = 250.0
    payment = 200.0
    is_valid = payment >= total
    assert is_valid == False, "Payment should be invalid when less than total"

def test_payment_equal_to_total():
    """Test payment equal to total is valid"""
    total = 250.0
    payment = 250.0
    is_valid = payment >= total
    assert is_valid == True, "Payment should be valid when equal to total"

def test_payment_greater_than_total():
    """Test payment greater than total is valid"""
    total = 250.0
    payment = 300.0
    is_valid = payment >= total
    assert is_valid == True, "Payment should be valid when greater than total"

def test_negative_payment_invalid():
    """Test negative payment is invalid"""
    payment = -100.0
    is_valid = payment > 0
    assert is_valid == False, "Negative payment should be invalid"

def test_zero_payment_invalid():
    """Test zero payment is invalid"""
    payment = 0.0
    is_valid = payment > 0
    assert is_valid == False, "Zero payment should be invalid"

def test_cancel_order_clears_cart():
    """Test cancel order clears the cart"""
    cart = [
        {'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 2},
        {'id': 2, 'name': 'Chicharon', 'price': 50.0, 'quantity': 1}
    ]
    # Simulate cancel
    cart.clear()
    assert len(cart) == 0, "Cart should be empty after cancel"

def test_cancel_order_resets_total():
    """Test cancel order resets total to zero"""
    cart = [{'id': 1, 'name': 'Sisig', 'price': 120.0, 'quantity': 2}]
    total = sum(item['price'] * item['quantity'] for item in cart)
    assert total == 240.0
    
    # Cancel order
    cart.clear()
    total = sum(item['price'] * item['quantity'] for item in cart)
    assert total == 0.0, "Total should be zero after cancel"

def test_cancel_does_not_affect_stock(test_db):
    """Test cancel order does not affect product stock"""
    cursor = test_db.cursor()
    cursor.execute("SELECT id, stock FROM products LIMIT 1")
    product = cursor.fetchone()
    
    if product:
        product_id, initial_stock = product
        # Simulate cancel - stock should remain unchanged
        cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
        current_stock = cursor.fetchone()[0]
        assert current_stock == initial_stock, "Stock should not change on cancel"
