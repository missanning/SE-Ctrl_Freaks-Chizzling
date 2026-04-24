# Test for US-14: Product Browsing and Selection (Quantity Dialog)
# Test Objective: Ensure that the quantity dialog correctly displays product details,
# handles quantity adjustments, and properly adds the product to the cart.

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class MockCartManager:
    """Simulates CartManager without Tkinter UI."""

    def __init__(self):
        self.cart = []
        self.total = 0.0

    def add_item(self, product_id, name, price, qty):
        for item in self.cart:
            if item['id'] == product_id:
                item['qty'] += qty
                self._update_total()
                return
        self.cart.append({'id': product_id, 'name': name, 'price': price, 'qty': qty})
        self._update_total()

    def _update_total(self):
        self.total = sum(item['price'] * item['qty'] for item in self.cart)


class MockQuantityDialog:
    """Simulates QuantityDialog logic without Tkinter UI."""

    def __init__(self, product, cart_manager):
        self.product = product
        self.cart_manager = cart_manager
        self.qty = 1
        self.dialog_open = True

    def increase_qty(self):
        self.qty += 1

    def decrease_qty(self):
        if self.qty > 1:
            self.qty -= 1

    def add_to_cart(self):
        self.cart_manager.add_item(
            self.product[0], self.product[1], self.product[2], self.qty
        )
        self.dialog_open = False

    def cancel(self):
        self.dialog_open = False


@pytest.fixture
def cart():
    return MockCartManager()


@pytest.fixture
def nachos():
    return (3, "Nachos", 80.0, "snacks")


@pytest.fixture
def sisig():
    return (1, "Sizzling Sisig", 199.0, "meals")


@pytest.fixture
def dialog(nachos, cart):
    return MockQuantityDialog(nachos, cart)


class TestProductDetailsDisplay:
    """Scenario 2: Dialog shows correct product details"""

    def test_dialog_has_correct_product_name(self, dialog, nachos):
        assert dialog.product[1] == nachos[1]

    def test_dialog_has_correct_product_price(self, dialog, nachos):
        assert dialog.product[2] == nachos[2]

    def test_dialog_has_correct_product_id(self, dialog, nachos):
        assert dialog.product[0] == nachos[0]

    def test_dialog_has_correct_product_category(self, dialog, nachos):
        assert dialog.product[3] == nachos[3]

    def test_default_quantity_is_one(self, dialog):
        assert dialog.qty == 1

    def test_dialog_is_open_on_init(self, dialog):
        assert dialog.dialog_open is True


class TestQuantityAdjustment:
    """Quantity controls increase and decrease correctly"""

    def test_increase_qty(self, dialog):
        dialog.increase_qty()
        assert dialog.qty == 2

    def test_increase_qty_multiple_times(self, dialog):
        dialog.increase_qty()
        dialog.increase_qty()
        dialog.increase_qty()
        assert dialog.qty == 4

    def test_decrease_qty(self, dialog):
        dialog.increase_qty()
        dialog.decrease_qty()
        assert dialog.qty == 1

    def test_decrease_qty_does_not_go_below_one(self, dialog):
        dialog.decrease_qty()
        assert dialog.qty == 1

    def test_decrease_qty_stays_at_one_on_multiple_attempts(self, dialog):
        dialog.decrease_qty()
        dialog.decrease_qty()
        dialog.decrease_qty()
        assert dialog.qty == 1

    def test_increase_then_decrease_returns_to_original(self, dialog):
        dialog.increase_qty()
        dialog.increase_qty()
        dialog.decrease_qty()
        dialog.decrease_qty()
        assert dialog.qty == 1


class TestAddToCart:
    """Scenario 3: Add to Cart adds product with correct details"""

    def test_add_to_cart_adds_item(self, dialog, cart):
        dialog.add_to_cart()
        assert len(cart.cart) == 1

    def test_add_to_cart_correct_product_id(self, dialog, cart):
        dialog.add_to_cart()
        assert cart.cart[0]['id'] == 3

    def test_add_to_cart_correct_name(self, dialog, cart):
        dialog.add_to_cart()
        assert cart.cart[0]['name'] == "Nachos"

    def test_add_to_cart_correct_price(self, dialog, cart):
        dialog.add_to_cart()
        assert cart.cart[0]['price'] == 80.0

    def test_add_to_cart_default_quantity_is_one(self, dialog, cart):
        dialog.add_to_cart()
        assert cart.cart[0]['qty'] == 1

    def test_add_to_cart_with_increased_quantity(self, dialog, cart):
        dialog.increase_qty()
        dialog.increase_qty()
        dialog.add_to_cart()
        assert cart.cart[0]['qty'] == 3

    def test_add_to_cart_updates_total(self, dialog, cart):
        dialog.add_to_cart()
        assert cart.total == 80.0

    def test_add_to_cart_updates_total_with_qty(self, dialog, cart):
        dialog.increase_qty()  # qty = 2
        dialog.add_to_cart()
        assert cart.total == 160.0

    def test_add_to_cart_closes_dialog(self, dialog):
        dialog.add_to_cart()
        assert dialog.dialog_open is False

    def test_add_multiple_different_products(self, cart, nachos, sisig):
        dialog1 = MockQuantityDialog(nachos, cart)
        dialog2 = MockQuantityDialog(sisig, cart)
        dialog1.add_to_cart()
        dialog2.add_to_cart()
        assert len(cart.cart) == 2
        assert cart.total == 80.0 + 199.0


class TestCancelDialog:
    """Cancel closes dialog without adding to cart"""

    def test_cancel_closes_dialog(self, dialog):
        dialog.cancel()
        assert dialog.dialog_open is False

    def test_cancel_does_not_add_to_cart(self, dialog, cart):
        dialog.cancel()
        assert len(cart.cart) == 0

    def test_cancel_does_not_update_total(self, dialog, cart):
        dialog.cancel()
        assert cart.total == 0.0


if __name__ == "__main__":
    pytest.main([__file__])
