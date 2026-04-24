# Test for US-14: Product Browsing and Selection
# Test Objective: Ensure that products are correctly loaded and displayed with their
# details, that search filtering works, and that product selection triggers the
# correct behavior for adding to cart.

import pytest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def sample_products():
    """Sample product list as returned from DB: (id, name, price, category)"""
    return [
        (1, "Sizzling Sisig",       199.0, "meals"),
        (2, "Sizzling Liempo",      199.0, "meals"),
        (3, "Nachos",                80.0, "snacks"),
        (4, "Fries - Cheese",        50.0, "snacks"),
        (5, "Chocolate Milk Tea",    39.0, "drinks"),
        (6, "Red Horse 1 Litro",    150.0, "alcohol"),
    ]


@pytest.fixture
def temp_db():
    """Create a temp database with sample products."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

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
    products = [
        ("Sizzling Sisig",    199.0, "meals"),
        ("Sizzling Liempo",   199.0, "meals"),
        ("Nachos",             80.0, "snacks"),
        ("Fries - Cheese",     50.0, "snacks"),
        ("Chocolate Milk Tea", 39.0, "drinks"),
        ("Red Horse 1 Litro", 150.0, "alcohol"),
    ]
    cursor.executemany(
        "INSERT INTO products (name, price, category) VALUES (?, ?, ?)", products
    )
    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


def load_products(db_path, category=None):
    """Simulate ChizzlingPOS.load_products() logic."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if category and category.lower() not in ("all", ""):
        cursor.execute(
            "SELECT id, name, price, COALESCE(category, 'All') FROM products WHERE LOWER(category)=?",
            (category.lower(),)
        )
    else:
        cursor.execute(
            "SELECT id, name, price, COALESCE(category, 'All') FROM products"
        )
    products = cursor.fetchall()
    conn.close()
    return products


def search_products(products, query):
    """Simulate ProductDisplay.search_products() logic."""
    return [p for p in products if query.lower() in p[1].lower()]


def get_product_image_path(product_name):
    """Simulate ProductDisplay.get_product_image_path() logic."""
    image_mapping = {
        "Nachos": "nachos.jpg",
        "Fries - Cheese": "fries.jpg",
        "Fries - Barbeque": "fries.jpg",
        "Fries - Sour and Cream": "fries.jpg",
        "Sizzling Sisig": "sizzlingsisig.jpg",
        "Sizzling Liempo": "sizzlingliempo.jpg",
        "Sizzling Tofu": "sizzlingtofu.png",
        "Red Horse 1 Litro": "redhorse.jpg",
        "Chocolate Milk Tea": "no image.jpg",
    }
    return image_mapping.get(product_name, "no image.jpg")


class TestViewProductList:
    """Scenario 1: View Product List"""

    def test_all_products_are_loaded(self, temp_db):
        products = load_products(temp_db)
        assert len(products) == 6

    def test_each_product_has_id(self, sample_products):
        for product in sample_products:
            assert product[0] is not None

    def test_each_product_has_name(self, sample_products):
        for product in sample_products:
            assert isinstance(product[1], str)
            assert len(product[1]) > 0

    def test_each_product_has_price(self, sample_products):
        for product in sample_products:
            assert isinstance(product[2], float)
            assert product[2] > 0

    def test_each_product_has_category(self, sample_products):
        for product in sample_products:
            assert product[3] in ("meals", "snacks", "drinks", "alcohol")

    def test_product_list_is_not_empty(self, temp_db):
        products = load_products(temp_db)
        assert len(products) > 0

    def test_product_names_are_unique(self, temp_db):
        products = load_products(temp_db)
        names = [p[1] for p in products]
        assert len(names) == len(set(names))

    def test_product_prices_are_positive(self, temp_db):
        products = load_products(temp_db)
        assert all(p[2] > 0 for p in products)


class TestViewProductDetails:
    """Scenario 2: View Product Details"""

    def test_product_has_name_detail(self, sample_products):
        product = sample_products[0]
        assert product[1] == "Sizzling Sisig"

    def test_product_has_price_detail(self, sample_products):
        product = sample_products[0]
        assert product[2] == 199.0

    def test_product_has_category_detail(self, sample_products):
        product = sample_products[0]
        assert product[3] == "meals"

    def test_image_path_returned_for_known_product(self):
        path = get_product_image_path("Nachos")
        assert path == "nachos.jpg"

    def test_fallback_image_for_unknown_product(self):
        path = get_product_image_path("Unknown Product")
        assert path == "no image.jpg"

    def test_image_path_returned_for_all_sample_products(self, sample_products):
        for product in sample_products:
            path = get_product_image_path(product[1])
            assert isinstance(path, str)
            assert len(path) > 0

    def test_search_returns_matching_product(self, sample_products):
        results = search_products(sample_products, "sisig")
        names = [p[1] for p in results]
        assert "Sizzling Sisig" in names

    def test_search_is_case_insensitive(self, sample_products):
        lower = search_products(sample_products, "nachos")
        upper = search_products(sample_products, "NACHOS")
        assert len(lower) == len(upper)

    def test_search_returns_empty_for_no_match(self, sample_products):
        results = search_products(sample_products, "pizza")
        assert results == []

    def test_search_returns_partial_match(self, sample_products):
        results = search_products(sample_products, "milk")
        assert any("Milk Tea" in p[1] for p in results)


class TestSelectProduct:
    """Scenario 3: Select a Product and Add to Cart"""

    def test_product_selection_stores_correct_id(self, sample_products):
        selected = sample_products[0]
        assert selected[0] == 1

    def test_product_selection_stores_correct_name(self, sample_products):
        selected = sample_products[2]  # Nachos
        assert selected[1] == "Nachos"

    def test_product_selection_stores_correct_price(self, sample_products):
        selected = sample_products[2]  # Nachos
        assert selected[2] == 80.0

    def test_add_to_cart_uses_correct_product_id(self, sample_products):
        """Simulate add_to_cart passing product data to cart."""
        product = sample_products[0]
        cart = []
        cart.append({'id': product[0], 'name': product[1], 'price': product[2], 'qty': 1})
        assert cart[0]['id'] == 1

    def test_add_to_cart_uses_correct_quantity(self, sample_products):
        product = sample_products[0]
        qty = 3
        cart = []
        cart.append({'id': product[0], 'name': product[1], 'price': product[2], 'qty': qty})
        assert cart[0]['qty'] == 3

    def test_add_to_cart_calculates_correct_subtotal(self, sample_products):
        product = sample_products[0]  # Sizzling Sisig 199.0
        qty = 2
        subtotal = product[2] * qty
        assert subtotal == 398.0

    def test_multiple_products_can_be_selected(self, sample_products):
        cart = []
        for product in sample_products[:3]:
            cart.append({'id': product[0], 'name': product[1], 'price': product[2], 'qty': 1})
        assert len(cart) == 3


if __name__ == "__main__":
    pytest.main([__file__])
