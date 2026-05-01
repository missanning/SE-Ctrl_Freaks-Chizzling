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
    return sqlite3.connect(db_path)


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
        # ── Header ──
        POSHeader(self.root, self.username, self.role, logout_cmd=self._logout)

        # ── Body: 3 columns ──
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=0)  # sidebar
        body.grid_columnconfigure(1, weight=1)  # products
        body.grid_columnconfigure(2, weight=0)  # cart
        body.grid_rowconfigure(0, weight=1)

        # Sidebar
        sidebar_frame = tk.Frame(body, bg=WHITE, width=140,
                                 highlightbackground=BORDER, highlightthickness=1)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.pack_propagate(False)
        self.category_nav = CategoryNavigation(sidebar_frame, self)

        # Products
        prod_frame = tk.Frame(body, bg=BG)
        prod_frame.grid(row=0, column=1, sticky="nsew")
        self.product_display = ProductDisplay(prod_frame, self)

        # Cart
        cart_frame = tk.Frame(body, bg=WHITE, width=380,
                              highlightbackground=BORDER, highlightthickness=1)
        cart_frame.grid(row=0, column=2, sticky="nsew")
        cart_frame.pack_propagate(False)
        self.cart_manager = CartManager(cart_frame, self)

    # ── Category loading ──────────────────────────────────────────────────────
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

    # ── Product loading (called by CategoryNavigation) ────────────────────────
    def load_products(self, category):
        conn = connect_db()
        cur  = conn.cursor()
        if category and category.lower() not in ("all", ""):
            cur.execute(
                "SELECT id, name, price, COALESCE(category,'All') FROM products "
                "WHERE LOWER(category)=?", (category.lower(),))
        else:
            cur.execute("SELECT id, name, price, COALESCE(category,'All') FROM products")
        self.products = cur.fetchall()
        conn.close()
        self.product_display.display_products(self.products)

    # ── Add to cart (called by ProductDisplay) ────────────────────────────────
    def add_to_cart(self, product):
        pid, name, price, *_ = product
        stock = self._get_stock(pid)
        if stock <= 0:
            messagebox.showerror("Out of Stock", f"'{name}' is currently out of stock.")
            return
        self.cart_manager.add_item(pid, name, price)

    # ── Payment processing (called by CartManager) ────────────────────────────
    def process_payment(self, cart, total, payment):
        change = payment - total
        conn   = connect_db()
        cur    = conn.cursor()
        now    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            "INSERT INTO transactions (total, payment, change, date) VALUES (?,?,?,?)",
            (total, payment, change, now))
        tid = cur.lastrowid

        for item in cart:
            sub = item["price"] * item["qty"]
            cur.execute(
                "INSERT INTO transaction_items "
                "(transaction_id, product_id, quantity, subtotal) VALUES (?,?,?,?)",
                (tid, item["id"], item["qty"], sub))
            cur.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item["qty"], item["id"]))

        conn.commit()
        conn.close()

        cart_snapshot = [(i["id"], i["name"], i["qty"] * i["price"], i["qty"]) for i in cart]
        self.cart_manager.clear_cart()
        show_receipt_window(self.root, tid, now, cart_snapshot, total, change)

    # ── Helpers ───────────────────────────────────────────────────────────────
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


def main():
    root = tk.Tk()
    ChizzlingPOS(root)
    root.mainloop()


if __name__ == "__main__":
    main()
