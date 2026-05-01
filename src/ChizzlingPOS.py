import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime

# Import modular components
from pos_header import POSHeader
from product_display import ProductDisplay
from category_navigation import CategoryNavigation
from cart_manager import CartManager
from quantity_dialog import QuantityDialog
from receipt_module import show_receipt_window

# Database connection
def connect_db():
    import os
    db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


class ChizzlingPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Chizzling POS System")
        self.root.configure(bg="#FAF3E1")
        self.root.state("zoomed")

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(4, weight=1)

        self.products = []
        self.setup_components()
        self.root.update()
        self.load_products()

    def setup_components(self):
        self.header = POSHeader(self.root)
        self.product_display = ProductDisplay(self.root, self)
        self.category_nav = CategoryNavigation(self.root, self)
        self.cart_manager = CartManager(self.root, self)

    def load_products(self, category=None):
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]

        if "category" not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'All'")
            conn.commit()

        if category and category.lower() not in ("all", ""):
            cursor.execute(
                "SELECT id, name, price, COALESCE(category, 'All') FROM products WHERE LOWER(category)=?",
                (category.lower(),)
            )
        else:
            cursor.execute(
                "SELECT id, name, price, COALESCE(category, 'All') FROM products"
            )

        self.products = cursor.fetchall()
        conn.close()

        self.product_display.display_products(self.products)

    def show_quantity_dialog(self, product):
        product_id = product[0]
        stock = self.get_stock(product_id)

        if stock <= 0:
            messagebox.showerror("Out of Stock", "This product is currently out of stock.")
            return

        QuantityDialog(
            self.root,
            product,
            self.cart_manager,
            self.product_display._img_cache
        )

    def cancel_order(self):
        self.cart_manager.cancel_order()

    def confirm_payment(self):
        try:
            payment = float(self.cart_manager.payment_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid payment amount")
            return

        if payment < self.cart_manager.total:
            messagebox.showerror("Error", "Insufficient payment")
            return

        change = payment - self.cart_manager.total

        conn = connect_db()
        cursor = conn.cursor()

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
            (self.cart_manager.total, payment, change, current_datetime)
        )

        transaction_id = cursor.lastrowid

        for item in self.cart_manager.cart:
            subtotal = item['price'] * item['qty']

            cursor.execute("""
                INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal)
                VALUES (?, ?, ?, ?)
            """, (transaction_id, item['id'], item['qty'], subtotal))

            # ✅ ONLY ONE DEDUCTION FUNCTION
            self.process_full_sale(
                cursor,
                item['id'],
                item['name'],
                item['qty']
            )

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", f"Transaction Saved! \nChange: ₱{change:.2f}")

        cart_data = [
            (item['id'], item['name'], item['qty'], item['price'] * item['qty'])
            for item in self.cart_manager.cart
        ]

        show_receipt_window(
            self.root,
            transaction_id,
            current_datetime,
            cart_data,
            self.cart_manager.total,
            change
        )

        self.cart_manager.clear_cart()

    def get_stock(self, product_id):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    # ✅ SINGLE SAFE STOCK HANDLER (NO DOUBLE DEDUCTION)
    def process_full_sale(self, cursor, product_id, product_name, quantity):

        # PRODUCT STOCK
        cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()

        cursor.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (quantity, product_id)
            )

        if not result:
            messagebox.showerror("Product Error", "Product not found.")
            return False

        current_stock = result[0]

        if current_stock < quantity:
            messagebox.showerror("Stock Error", "Not enough stock.")
            return False

        # INGREDIENT STOCK
        cursor.execute("""
            SELECT ingredient_name, quantity
            FROM recipe_ingredients
            WHERE product_name = ?
        """, (product_name,))

        recipe = cursor.fetchall()
        
        for ingredient_name, qty in recipe:
            total = quantity * qty

            cursor.execute("""
                UPDATE ingredients
                SET stock = stock - ?
                WHERE name = ?
            """, (total, ingredient_name))

            

        return True


def main():
    root = tk.Tk()
    app = ChizzlingPOS(root)
    root.mainloop()


if __name__ == "__main__":
    main()