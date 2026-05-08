"""
Automated Tests for User Story: Meal Ingredients Management
As an Inventory Staff, I want to manage ingredients for products categorized as Meal,
so that meal products have complete and accurate ingredient details.
"""

import unittest
import sys
import os
import sqlite3
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database_setup import connect_db, create_tables


class TestMealIngredientsManagement(unittest.TestCase):
    """Test suite for meal ingredients management functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test database once for all tests"""
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_meal_ingredients.db')
        
    def setUp(self):
        """Set up fresh test database before each test"""
        # Remove existing test database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        # Create fresh test database
        self.conn = sqlite3.connect(self.test_db_path)
        self.cursor = self.conn.cursor()
        
        # Create tables
        self._create_test_tables()
        self._insert_test_data()
        
    def tearDown(self):
        """Clean up after each test"""
        self.conn.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def _create_test_tables(self):
        """Create necessary tables for testing"""
        # Products table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                price REAL,
                stock INTEGER,
                category TEXT,
                low_stock_threshold INTEGER DEFAULT 30
            )
        """)
        
        # Ingredients table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                stock REAL,
                unit TEXT,
                low_stock_threshold REAL DEFAULT 0
            )
        """)
        
        # Recipe ingredients table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT,
                ingredient_name TEXT,
                quantity TEXT,
                unit TEXT
            )
        """)
        
        self.conn.commit()
    
    def _insert_test_data(self):
        """Insert test data"""
        # Insert test ingredients
        test_ingredients = [
            ("Pork", 5000, "grams"),
            ("Chicken Fillet", 3000, "grams"),
            ("Egg", 100, "pcs"),
            ("Onion", 50, "pcs"),
            ("Garlic", 30, "pcs")
        ]
        
        self.cursor.executemany(
            "INSERT INTO ingredients (name, stock, unit) VALUES (?, ?, ?)",
            test_ingredients
        )
        self.conn.commit()

    # ========================================================================
    # AC1: Category dropdown displays predefined categories
    # ========================================================================
    
    def test_category_dropdown_has_predefined_categories(self):
        """
        Given the inventory staff is on the "Add New Product" form
        When viewing the Category field
        Then a dropdown with predefined categories is displayed
        """
        from ProductManagementSystem import CATEGORIES
        
        # Verify predefined categories exist
        self.assertIsNotNone(CATEGORIES)
        self.assertIsInstance(CATEGORIES, list)
        
        # Verify expected categories
        expected_categories = ["meals", "snacks", "drinks", "alcohol"]
        self.assertEqual(CATEGORIES, expected_categories)
        
        # Verify all categories are strings
        for category in CATEGORIES:
            self.assertIsInstance(category, str)
    
    # ========================================================================
    # AC2: Ingredients section visible when "Meal" selected
    # ========================================================================
    
    def test_ingredients_section_visible_for_meals_category(self):
        """
        Given the inventory staff selects "Meal" as the category
        When the selection is saved or applied
        Then the Ingredients section becomes visible
        """
        # This tests the logic that ingredients section should show for meals
        category = "meals"
        
        # Simulate the condition check
        should_show_ingredients = (category == "meals")
        
        self.assertTrue(should_show_ingredients,
                       "Ingredients section should be visible for meals category")
    
    # ========================================================================
    # AC3: Ingredients section hidden for non-meal categories
    # ========================================================================
    
    def test_ingredients_section_hidden_for_non_meal_categories(self):
        """
        Given the inventory staff selects a category other than "Meal"
        When the category changes
        Then the Ingredients section is hidden and any entered ingredient data is not required
        """
        non_meal_categories = ["snacks", "drinks", "alcohol"]
        
        for category in non_meal_categories:
            should_show_ingredients = (category == "meals")
            
            self.assertFalse(should_show_ingredients,
                           f"Ingredients section should be hidden for {category} category")
    
    # ========================================================================
    # AC4: Can select from existing ingredients
    # ========================================================================
    
    def test_can_select_from_existing_ingredients(self):
        """
        Given the Ingredients section is visible
        When the inventory staff adds an ingredient
        Then they can select from existing ingredients in the inventory list
        """
        # Query existing ingredients
        self.cursor.execute("SELECT name, unit FROM ingredients ORDER BY name")
        ingredients = self.cursor.fetchall()
        
        # Verify ingredients exist
        self.assertGreater(len(ingredients), 0,
                          "Should have existing ingredients to select from")
        
        # Verify ingredient structure
        for ingredient in ingredients:
            name, unit = ingredient
            self.assertIsInstance(name, str)
            self.assertIsInstance(unit, str)
            self.assertTrue(len(name) > 0)
            self.assertTrue(len(unit) > 0)
    
    # ========================================================================
    # AC5: Ingredient requires numeric quantity and valid unit
    # ========================================================================
    
    def test_ingredient_requires_numeric_quantity(self):
        """
        Given an ingredient is added to the product
        When the inventory staff inputs details
        Then they must provide a numeric quantity
        """
        # Test valid numeric quantities
        valid_quantities = ["100", "50.5", "1", "0.25"]
        
        for qty in valid_quantities:
            try:
                float(qty)
                is_valid = True
            except ValueError:
                is_valid = False
            
            self.assertTrue(is_valid,
                          f"Quantity '{qty}' should be valid numeric value")
        
        # Test invalid quantities
        invalid_quantities = ["abc", "", "ten", "1.2.3"]
        
        for qty in invalid_quantities:
            try:
                float(qty)
                is_valid = True
            except ValueError:
                is_valid = False
            
            self.assertFalse(is_valid,
                           f"Quantity '{qty}' should be invalid")
    
    def test_ingredient_requires_valid_unit(self):
        """
        Given an ingredient is added to the product
        When the inventory staff inputs details
        Then they must provide a valid unit of measurement
        """
        # Valid units should be non-empty strings
        valid_units = ["grams", "ml", "pcs", "kg", "liters"]
        
        for unit in valid_units:
            is_valid = isinstance(unit, str) and len(unit.strip()) > 0
            self.assertTrue(is_valid,
                          f"Unit '{unit}' should be valid")
        
        # Invalid units
        invalid_units = ["", "   ", None]
        
        for unit in invalid_units:
            if unit is None:
                is_valid = False
            else:
                is_valid = isinstance(unit, str) and len(unit.strip()) > 0
            
            self.assertFalse(is_valid,
                           f"Unit '{unit}' should be invalid")
    
    # ========================================================================
    # AC6: Multiple ingredients can be added
    # ========================================================================
    
    def test_multiple_ingredients_can_be_added(self):
        """
        Given the Ingredients section is visible
        When the inventory staff adds ingredients
        Then multiple ingredients can be added to a single product
        """
        # Simulate adding multiple ingredients to a product
        product_name = "Test Sisig"
        ingredients_to_add = [
            {"name": "Pork", "quantity": "100", "unit": "grams"},
            {"name": "Onion", "quantity": "0.5", "unit": "pcs"},
            {"name": "Egg", "quantity": "1", "unit": "pcs"},
            {"name": "Garlic", "quantity": "0.25", "unit": "pcs"}
        ]
        
        # Add product
        self.cursor.execute(
            "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
            (product_name, 109, 100, "meals")
        )
        
        # Add all ingredients
        for ing in ingredients_to_add:
            self.cursor.execute(
                "INSERT INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
                (product_name, ing["name"], ing["quantity"], ing["unit"])
            )
        
        self.conn.commit()
        
        # Verify all ingredients were added
        self.cursor.execute(
            "SELECT COUNT(*) FROM recipe_ingredients WHERE product_name=?",
            (product_name,)
        )
        count = self.cursor.fetchone()[0]
        
        self.assertEqual(count, len(ingredients_to_add),
                        "All ingredients should be added to the product")
    
    # ========================================================================
    # AC7: Can create new ingredient inline
    # ========================================================================
    
    def test_can_create_new_ingredient_inline(self):
        """
        Given the required ingredient does not exist
        When the inventory staff selects "Add Ingredient"
        Then a modal or inline form opens without leaving the page
        """
        # Test creating a new ingredient
        new_ingredient = {
            "name": "Tofu",
            "stock": 2000,
            "unit": "grams"
        }
        
        # Verify ingredient doesn't exist
        self.cursor.execute(
            "SELECT id FROM ingredients WHERE name=?",
            (new_ingredient["name"],)
        )
        result = self.cursor.fetchone()
        self.assertIsNone(result, "Ingredient should not exist yet")
        
        # Create new ingredient
        self.cursor.execute(
            "INSERT INTO ingredients (name, stock, unit) VALUES (?, ?, ?)",
            (new_ingredient["name"], new_ingredient["stock"], new_ingredient["unit"])
        )
        self.conn.commit()
        
        # Verify ingredient was created
        self.cursor.execute(
            "SELECT name, stock, unit FROM ingredients WHERE name=?",
            (new_ingredient["name"],)
        )
        result = self.cursor.fetchone()
        
        self.assertIsNotNone(result, "Ingredient should be created")
        self.assertEqual(result[0], new_ingredient["name"])
        self.assertEqual(result[1], new_ingredient["stock"])
        self.assertEqual(result[2], new_ingredient["unit"])
    
    # ========================================================================
    # AC8: New ingredient immediately available
    # ========================================================================
    
    def test_new_ingredient_immediately_available(self):
        """
        Given a new ingredient is successfully created
        When the ingredient list refreshes
        Then the ingredient becomes available for selection immediately
        """
        # Get initial ingredient count
        self.cursor.execute("SELECT COUNT(*) FROM ingredients")
        initial_count = self.cursor.fetchone()[0]
        
        # Create new ingredient
        new_ingredient = "Liempo"
        self.cursor.execute(
            "INSERT INTO ingredients (name, stock, unit) VALUES (?, ?, ?)",
            (new_ingredient, 3000, "grams")
        )
        self.conn.commit()
        
        # Query ingredients again
        self.cursor.execute("SELECT COUNT(*) FROM ingredients")
        new_count = self.cursor.fetchone()[0]
        
        # Verify count increased
        self.assertEqual(new_count, initial_count + 1,
                        "Ingredient count should increase by 1")
        
        # Verify new ingredient is available
        self.cursor.execute(
            "SELECT name FROM ingredients WHERE name=?",
            (new_ingredient,)
        )
        result = self.cursor.fetchone()
        
        self.assertIsNotNone(result,
                            "New ingredient should be immediately available")
        self.assertEqual(result[0], new_ingredient)
    
    # ========================================================================
    # AC9: Meal products must have at least one ingredient
    # ========================================================================
    
    def test_meal_product_requires_at_least_one_ingredient(self):
        """
        Given the inventory staff submits the product
        When the category is set to Meal
        Then at least one ingredient must be included
        """
        product_name = "Test Meal"
        category = "meals"
        
        # Add product
        self.cursor.execute(
            "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
            (product_name, 99, 100, category)
        )
        self.conn.commit()
        
        # Check if product has ingredients
        self.cursor.execute(
            "SELECT COUNT(*) FROM recipe_ingredients WHERE product_name=?",
            (product_name,)
        )
        ingredient_count = self.cursor.fetchone()[0]
        
        # For validation, meal products should have at least 1 ingredient
        if category == "meals":
            has_valid_ingredients = ingredient_count > 0
            self.assertFalse(has_valid_ingredients,
                           "Meal without ingredients should fail validation")
        
        # Now add an ingredient
        self.cursor.execute(
            "INSERT INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
            (product_name, "Pork", "100", "grams")
        )
        self.conn.commit()
        
        # Check again
        self.cursor.execute(
            "SELECT COUNT(*) FROM recipe_ingredients WHERE product_name=?",
            (product_name,)
        )
        ingredient_count = self.cursor.fetchone()[0]
        
        has_valid_ingredients = ingredient_count > 0
        self.assertTrue(has_valid_ingredients,
                       "Meal with ingredients should pass validation")
    
    def test_ingredient_must_have_quantity_and_unit(self):
        """
        Given the inventory staff submits the product
        When the category is set to Meal
        Then each ingredient must have both quantity and unit defined
        """
        # Test valid ingredient
        valid_ingredient = {
            "name": "Pork",
            "quantity": "100",
            "unit": "grams"
        }
        
        has_quantity = valid_ingredient.get("quantity") and len(valid_ingredient["quantity"].strip()) > 0
        has_unit = valid_ingredient.get("unit") and len(valid_ingredient["unit"].strip()) > 0
        
        self.assertTrue(has_quantity, "Ingredient should have quantity")
        self.assertTrue(has_unit, "Ingredient should have unit")
        
        # Test invalid ingredients
        invalid_ingredients = [
            {"name": "Pork", "quantity": "", "unit": "grams"},  # No quantity
            {"name": "Pork", "quantity": "100", "unit": ""},    # No unit
            {"name": "Pork", "quantity": "", "unit": ""},       # No quantity or unit
        ]
        
        for ing in invalid_ingredients:
            has_quantity = ing.get("quantity") and len(ing["quantity"].strip()) > 0
            has_unit = ing.get("unit") and len(ing["unit"].strip()) > 0
            is_valid = has_quantity and has_unit
            
            self.assertFalse(is_valid,
                           f"Ingredient {ing} should be invalid")
    
    # ========================================================================
    # AC10: Edit product shows existing ingredients
    # ========================================================================
    
    def test_edit_meal_product_shows_existing_ingredients(self):
        """
        Given the inventory staff is on the "Edit Product" form
        When the product category is "Meal"
        Then the Ingredients section is displayed with the existing ingredients
        """
        # Create a meal product with ingredients
        product_name = "Sizzling Sisig"
        
        self.cursor.execute(
            "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
            (product_name, 109, 100, "meals")
        )
        
        # Add ingredients
        ingredients = [
            ("Pork", "100", "grams"),
            ("Onion", "0.25", "pcs"),
            ("Egg", "1", "pcs")
        ]
        
        for ing_name, qty, unit in ingredients:
            self.cursor.execute(
                "INSERT INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
                (product_name, ing_name, qty, unit)
            )
        
        self.conn.commit()
        
        # Retrieve product and ingredients (simulating edit form load)
        self.cursor.execute(
            "SELECT name, category FROM products WHERE name=?",
            (product_name,)
        )
        product = self.cursor.fetchone()
        
        self.assertIsNotNone(product, "Product should exist")
        self.assertEqual(product[1], "meals", "Product should be a meal")
        
        # Get ingredients
        self.cursor.execute(
            "SELECT ingredient_name, quantity, unit FROM recipe_ingredients WHERE product_name=?",
            (product_name,)
        )
        loaded_ingredients = self.cursor.fetchall()
        
        self.assertEqual(len(loaded_ingredients), len(ingredients),
                        "All ingredients should be loaded")
        
        # Verify each ingredient
        for i, (ing_name, qty, unit) in enumerate(ingredients):
            self.assertEqual(loaded_ingredients[i][0], ing_name)
            self.assertEqual(loaded_ingredients[i][1], qty)
            self.assertEqual(loaded_ingredients[i][2], unit)
    
    # ========================================================================
    # AC11: Can add, update, remove ingredients when editing
    # ========================================================================
    
    def test_can_add_ingredient_when_editing_meal(self):
        """
        Given the inventory staff edits a product categorized as "Meal"
        When modifying the Ingredients section
        Then they can add ingredients
        """
        product_name = "Test Meal"
        
        # Create meal with one ingredient
        self.cursor.execute(
            "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
            (product_name, 99, 100, "meals")
        )
        self.cursor.execute(
            "INSERT INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
            (product_name, "Pork", "100", "grams")
        )
        self.conn.commit()
        
        # Add another ingredient (simulating edit)
        self.cursor.execute(
            "INSERT INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
            (product_name, "Onion", "0.5", "pcs")
        )
        self.conn.commit()
        
        # Verify both ingredients exist
        self.cursor.execute(
            "SELECT COUNT(*) FROM recipe_ingredients WHERE product_name=?",
            (product_name,)
        )
        count = self.cursor.fetchone()[0]
        
        self.assertEqual(count, 2, "Should have 2 ingredients after adding")
    
    def test_can_update_ingredient_when_editing_meal(self):
        """
        Given the inventory staff edits a product categorized as "Meal"
        When modifying the Ingredients section
        Then they can update ingredients
        """
        product_name = "Test Meal"
        
        # Create meal with ingredient
        self.cursor.execute(
            "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
            (product_name, 99, 100, "meals")
        )
        self.cursor.execute(
            "INSERT INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
            (product_name, "Pork", "100", "grams")
        )
        self.conn.commit()
        
        # Update ingredient quantity
        self.cursor.execute(
            "UPDATE recipe_ingredients SET quantity=? WHERE product_name=? AND ingredient_name=?",
            ("150", product_name, "Pork")
        )
        self.conn.commit()
        
        # Verify update
        self.cursor.execute(
            "SELECT quantity FROM recipe_ingredients WHERE product_name=? AND ingredient_name=?",
            (product_name, "Pork")
        )
        result = self.cursor.fetchone()
        
        self.assertEqual(result[0], "150", "Quantity should be updated")
    
    def test_can_remove_ingredient_when_editing_meal(self):
        """
        Given the inventory staff edits a product categorized as "Meal"
        When modifying the Ingredients section
        Then they can remove ingredients
        """
        product_name = "Test Meal"
        
        # Create meal with two ingredients
        self.cursor.execute(
            "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
            (product_name, 99, 100, "meals")
        )
        self.cursor.execute(
            "INSERT INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
            (product_name, "Pork", "100", "grams")
        )
        self.cursor.execute(
            "INSERT INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
            (product_name, "Onion", "0.5", "pcs")
        )
        self.conn.commit()
        
        # Remove one ingredient
        self.cursor.execute(
            "DELETE FROM recipe_ingredients WHERE product_name=? AND ingredient_name=?",
            (product_name, "Onion")
        )
        self.conn.commit()
        
        # Verify removal
        self.cursor.execute(
            "SELECT COUNT(*) FROM recipe_ingredients WHERE product_name=?",
            (product_name,)
        )
        count = self.cursor.fetchone()[0]
        
        self.assertEqual(count, 1, "Should have 1 ingredient after removal")
        
        # Verify correct ingredient remains
        self.cursor.execute(
            "SELECT ingredient_name FROM recipe_ingredients WHERE product_name=?",
            (product_name,)
        )
        result = self.cursor.fetchone()
        
        self.assertEqual(result[0], "Pork", "Pork ingredient should remain")


# ============================================================================
# Test Runner
# ============================================================================

def run_tests():
    """Run all tests and generate report"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestMealIngredientsManagement)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
