# Test for US-12: Cart Management
# Test Objective: Ensure that items can be added, quantity adjusted, removed from cart,
# and that totals and change are automatically recalculated on every cart change.

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class MockCart:
    """Simulates CartManager cart logic without Tkinter UI."""

    def __init__(self):
        self.cart = []
        self.total = 0

    def add_item(self, product_id, name, price, qty):
        for item in self.cart:
            if item['id'] == product_id:
                item['qty'] += qty
                self._update_total()
                return
        self.cart.append({'id': product_id, 'name': name, 'price': price, 'qty': qty})
        self._update_total()

    def change_qty(self, index, delta):
        self.cart[index]['qty'] += delta
        if self.cart[index]['qty'] <= 0:
            self.cart.pop(index)
        self._update_total()

    def remove_item(self, index):
        self.cart.pop(index)
        self._update_total()

    def clear_cart(self):
        self.cart = []
        self._update_total()

    def _update_total(self):
        self.total = sum(item['price'] * item['qty'] for item in self.cart)

    def calculate_change(self, payment):
        return payment - self.total


@pytest.fixture
def cart():
    return MockCart()


@pytest.fixture
def cart_with_items(cart):
    cart.add_item(1, "Sizzling Sisig", 199.0, 1)
    cart.add_item(2, "Nachos", 80.0, 2)
    cart.add_item(3, "Milk Tea", 39.0, 1)
    return cart


class TestAddItemToCart:
    """AC1: Add item to cart and total is automatically updated"""

    def test_add_single_item(self, cart):
        cart.add_item(1, "Sizzling Sisig", 199.0, 1)
        assert len(cart.cart) == 1

    def test_added_item_has_correct_name(self, cart):
        cart.add_item(1, "Sizzling Sisig", 199.0, 1)
        assert cart.cart[0]['name'] == "Sizzling Sisig"

    def test_added_item_has_correct_price(self, cart):
        cart.add_item(1, "Sizzling Sisig", 199.0, 1)
        assert cart.cart[0]['price'] == 199.0

    def test_added_item_has_correct_quantity(self, cart):
        cart.add_item(1, "Sizzling Sisig", 199.0, 2)
        assert cart.cart[0]['qty'] == 2

    def test_total_updates_after_adding_item(self, cart):
        cart.add_item(1, "Sizzling Sisig", 199.0, 1)
        assert cart.total == 199.0

    def test_total_updates_after_adding_multiple_items(self, cart):
        cart.add_item(1, "Sizzling Sisig", 199.0, 1)
        cart.add_item(2, "Nachos", 80.0, 1)
        assert cart.total == 279.0

    def test_adding_same_item_increases_quantity(self, cart):
        cart.add_item(1, "Sizzling Sisig", 199.0, 1)
        cart.add_item(1, "Sizzling Sisig", 199.0, 2)
        assert len(cart.cart) == 1
        assert cart.cart[0]['qty'] == 3

    def test_adding_same_item_updates_total(self, cart):
        cart.add_item(1, "Sizzling Sisig", 199.0, 1)
        cart.add_item(1, "Sizzling Sisig", 199.0, 1)
        assert cart.total == 398.0


class TestAdjustItemQuantity:
    """AC2: Adjust item quantity recalculates subtotal and total"""

    def test_increase_quantity(self, cart_with_items):
        cart_with_items.change_qty(0, 1)  # Sizzling Sisig qty: 1 -> 2
        assert cart_with_items.cart[0]['qty'] == 2

    def test_decrease_quantity(self, cart_with_items):
        cart_with_items.change_qty(1, -1)  # Nachos qty: 2 -> 1
        assert cart_with_items.cart[1]['qty'] == 1

    def test_total_recalculates_after_increase(self, cart_with_items):
        original_total = cart_with_items.total
        cart_with_items.change_qty(0, 1)  # +199.0
        assert cart_with_items.total == original_total + 199.0

    def test_total_recalculates_after_decrease(self, cart_with_items):
        original_total = cart_with_items.total
        cart_with_items.change_qty(1, -1)  # -80.0
        assert cart_with_items.total == original_total - 80.0

    def test_item_removed_when_quantity_reaches_zero(self, cart_with_items):
        cart_with_items.change_qty(1, -2)  # Nachos qty: 2 -> 0
        names = [item['name'] for item in cart_with_items.cart]
        assert "Nachos" not in names

    def test_item_removed_when_quantity_goes_negative(self, cart_with_items):
        cart_with_items.change_qty(0, -5)  # qty goes below 0
        names = [item['name'] for item in cart_with_items.cart]
        assert "Sizzling Sisig" not in names

    def test_total_updates_after_item_removed_via_qty(self, cart_with_items):
        cart_with_items.change_qty(1, -2)  # Remove Nachos (80 x 2 = 160)
        assert cart_with_items.total == 199.0 + 39.0


class TestRemoveItemFromCart:
    """AC3: Remove item from cart and total is adjusted"""

    def test_remove_item_decreases_cart_length(self, cart_with_items):
        cart_with_items.remove_item(0)
        assert len(cart_with_items.cart) == 2

    def test_correct_item_is_removed(self, cart_with_items):
        cart_with_items.remove_item(0)  # Remove Sizzling Sisig
        names = [item['name'] for item in cart_with_items.cart]
        assert "Sizzling Sisig" not in names

    def test_total_adjusts_after_removal(self, cart_with_items):
        cart_with_items.remove_item(0)  # Remove Sizzling Sisig (199.0)
        assert cart_with_items.total == 80.0 * 2 + 39.0

    def test_cart_empty_after_removing_all_items(self, cart):
        cart.add_item(1, "Nachos", 80.0, 1)
        cart.remove_item(0)
        assert len(cart.cart) == 0

    def test_total_is_zero_after_removing_all_items(self, cart):
        cart.add_item(1, "Nachos", 80.0, 1)
        cart.remove_item(0)
        assert cart.total == 0.0

    def test_clear_cart_removes_all_items(self, cart_with_items):
        cart_with_items.clear_cart()
        assert len(cart_with_items.cart) == 0

    def test_total_is_zero_after_clear_cart(self, cart_with_items):
        cart_with_items.clear_cart()
        assert cart_with_items.total == 0.0


class TestAutomaticTotalAndChange:
    """AC4: Automatic total and change calculation"""

    def test_total_correct_with_multiple_items(self, cart_with_items):
        # Sisig(199x1) + Nachos(80x2) + MilkTea(39x1) = 398
        assert cart_with_items.total == 199.0 + 160.0 + 39.0

    def test_change_calculated_correctly(self, cart_with_items):
        change = cart_with_items.calculate_change(500.0)
        assert change == 500.0 - cart_with_items.total

    def test_change_is_zero_for_exact_payment(self, cart_with_items):
        change = cart_with_items.calculate_change(cart_with_items.total)
        assert change == 0.0

    def test_total_updates_on_add(self, cart):
        cart.add_item(1, "Nachos", 80.0, 1)
        assert cart.total == 80.0
        cart.add_item(2, "Milk Tea", 39.0, 1)
        assert cart.total == 119.0

    def test_total_updates_on_qty_change(self, cart):
        cart.add_item(1, "Nachos", 80.0, 1)
        cart.change_qty(0, 2)
        assert cart.total == 240.0

    def test_total_updates_on_remove(self, cart):
        cart.add_item(1, "Nachos", 80.0, 1)
        cart.add_item(2, "Milk Tea", 39.0, 1)
        cart.remove_item(0)
        assert cart.total == 39.0

    def test_total_is_zero_on_empty_cart(self, cart):
        assert cart.total == 0.0


if __name__ == "__main__":
    pytest.main([__file__])
