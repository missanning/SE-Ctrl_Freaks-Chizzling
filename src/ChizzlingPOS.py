import tkinter as tk
from tkinter import messagebox
import sqlite3
import os
from datetime import datetime

from receipt_module       import show_receipt_window
from pos_header           import POSHeader
from category_navigation  import CategoryNavigation
from product_display      import ProductDisplay
from cart_manager         import CartManager

BG     = "#FFF8EE"
WHITE  = "#FFFFFF"
BORDER = "#FFD966"


def connect_db():
    db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


class ChizzlingPOS:
    def __init__(self, root, username="cashier", role="cashier"):
        self.root     = root
        self.username = username
        self.role     = role
        self.products = []

        self.root.title("Chizzling POS System")
        self.root.configure(bg=BG)
        self.root.state("zoomed")

        self._build_ui()
        self.root.update()
        self._load_categories()
        self.load_products(None)

    def _build_ui(self):
        POSHeader(self.root, self.username, self.role, logout_cmd=self._logout)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=0)
        body.grid_rowconfigure(0, weight=1)

        sidebar_frame = tk.Frame(body, bg=WHITE, width=140,
                                 highlightbackground=BORDER, highlightthickness=1)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.pack_propagate(False)
        self.category_nav = CategoryNavigation(sidebar_frame, self)

        prod_frame = tk.Frame(body, bg=BG)
        prod_frame.grid(row=0, column=1, sticky="nsew")
        self.product_display = ProductDisplay(prod_frame, self)

        cart_frame = tk.Frame(body, bg=WHITE, width=380,
                              highlightbackground=BORDER, highlightthickness=1)
        cart_frame.grid(row=0, column=2, sticky="nsew")
        cart_frame.pack_propagate(False)
        self.cart_manager = CartManager(cart_frame, self)

    def _load_categories(self):
        conn = connect_db()
        cur  = conn.cursor()
        cur.execute("PRAGMA table_info(products)")
        cols = [r[1] for r in cur.fetchall()]

        if "category" not in cols:
            cur.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'All'")
            conn.commit()

        cur.execute("SELECT DISTINCT COALESCE(category,'All') FROM products")
        cats = ["All"] + sorted({r[0] for r in cur.fetchall()
                                  if r[0] not in ("All", "unknown", "")})
        conn.close()
        self.category_nav.load_categories(cats)

    def load_products(self, category):
        conn = connect_db()
        cur  = conn.cursor()

        if category and category.lower() not in ("all", ""):
            cur.execute(
                "SELECT id, name, price, COALESCE(category,'All') FROM products "
                "WHERE LOWER(category)=?", (category.lower(),))
        else:
            cur.execute(
                "SELECT id, name, price, COALESCE(category,'All') FROM products"
            )

        self.products = cur.fetchall()
        conn.close()
        # Preload images in background before rendering
        self.product_display.preload_images([p[1] for p in self.products])
        self.product_display.display_products(self.products)

    def add_to_cart(self, product):
        pid, name, price, *_ = product
        stock = self._get_stock(pid)

        if stock <= 0:
            messagebox.showerror("Out of Stock", f"'{name}' is currently out of stock.")
            return

        self.cart_manager.add_item(pid, name, price)

    def process_payment(self, cart, total, payment):
        change = payment - total
        conn   = connect_db()
        cur    = conn.cursor()
        now    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            "INSERT INTO transactions (total, payment, change, date) VALUES (?,?,?,?)",
            (total, payment, change, now)
        )

        tid = cur.lastrowid

        for item in cart:
            sub = item["price"] * item["qty"]

            cur.execute(
                "INSERT INTO transaction_items "
                "(transaction_id, product_id, quantity, subtotal) VALUES (?,?,?,?)",
                (tid, item["id"], item["qty"], sub)
            )

            # ❌ REMOVED duplicate product deduction here

            self.process_full_sale(
                cur,
                item['id'],
                item['name'],
                item['qty']
            )

        conn.commit()
        conn.close()

        cart_snapshot = [
            (i["id"], i["name"], i["qty"] * i["price"], i["qty"])
            for i in cart
        ]

        self.cart_manager.clear_cart()

        show_receipt_window(
            self.root, tid, now, cart_snapshot, total, change
        )

    def _get_stock(self, pid):
        conn = connect_db()
        cur  = conn.cursor()
        cur.execute("SELECT stock FROM products WHERE id=?", (pid,))
        result = cur.fetchone()
        conn.close()
        return result[0] if result else 0

    def _logout(self):
        self.root.destroy()
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        from LoginPage import MainApp
        new_root = tk.Tk()
        MainApp(new_root)
        new_root.mainloop()
    
    def process_full_sale(self, cursor, product_id, product_name, quantity):

        # STEP 1: VERIFY PRODUCT STOCK
        cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Product Error", "Product not found.")
            return False

        current_stock = result[0]

        if current_stock < quantity:
            messagebox.showerror("Stock Error", "Not enough stock.")
            return False

        # STEP 2: DEDUCT PRODUCT STOCK
        cursor.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (quantity, product_id)
        )

        # STEP 3: GET RECIPE (IMPORTANT FIX HERE)
        cursor.execute("""
            SELECT ingredient_name, quantity
            FROM recipe_ingredients
            WHERE TRIM(LOWER(product_name)) = TRIM(LOWER(?))
        """, (product_name,))

        recipe = cursor.fetchall()

        if not recipe:
            print(f"⚠️ No recipe found for: {product_name}")
            return False

        # STEP 4: DEDUCT INGREDIENTS
        for ingredient_name, qty in recipe:

            total = quantity * qty

            print(f"Deducting {total} from {ingredient_name}")

            cursor.execute("""
                UPDATE ingredients
                SET stock = COALESCE(stock, 0) - ?
                WHERE TRIM(LOWER(name)) = TRIM(LOWER(?))
            """, (total, ingredient_name))

            if cursor.rowcount == 0:
                print(f"⚠️ Ingredient NOT found in table: {ingredient_name}")

        return True

def main():
    root = tk.Tk()
    ChizzlingPOS(root)
    root.mainloop()

if __name__ == "__main__":
    main()