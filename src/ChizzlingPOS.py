import tkinter as tk
from tkinter import messagebox
import sqlite3
import os
import sys
from datetime import datetime

from receipt_module       import show_receipt_window
from pos_header           import POSHeader
from category_navigation  import CategoryNavigation
from product_display      import ProductDisplay
from cart_manager         import CartManager
from database_setup       import connect_db

BG     = "#FFF8EE"
WHITE  = "#FFFFFF"
BORDER = "#FFD966"


class ChizzlingPOS:
    def __init__(self, root, username="cashier", role="cashier"):
        self.root     = root
        self.username = username
        self.role     = role
        self.products = []

        self.root.title("Chizzling POS System")
        self.root.configure(bg=BG)
        self.root.state("zoomed")
        
        # Set window icon
        self._set_window_icon()

        self._build_ui()
        self.root.update()
        self._load_categories()
        self.load_products(None)

    def _set_window_icon(self):
        """Set the window icon for the application."""
        try:
            icon_path = self._get_asset_path("LOGO.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                # Also set as default icon for all Toplevel windows
                self.root.iconbitmap(default=icon_path)
        except Exception as e:
            print(f"Failed to set window icon: {e}")

    def _get_asset_path(self, filename):
        """Get the correct path for assets, handling both dev and bundled executable."""
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, "assets", filename)
            else:
                return os.path.join(os.path.dirname(sys.executable), "assets", filename)
        else:
            return os.path.join(os.path.dirname(__file__), "..", "assets", filename)

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
        
        # Preload ALL images synchronously before displaying
        product_names = [p[1] for p in self.products]
        self._preload_all_images_sync(product_names)
        
        self.product_display.display_products(self.products)
    
    def _preload_all_images_sync(self, product_names):
        """Preload all images synchronously (blocks UI but ensures all images ready)."""
        from product_display import _get_image_filename, ASSETS_DIR, CARD_IMG_W, CARD_IMG_H, PIL_AVAILABLE
        if not PIL_AVAILABLE:
            return
        
        from PIL import Image, ImageTk
        for name in product_names:
            filename = _get_image_filename(name)
            path = os.path.join(ASSETS_DIR, filename)
            key = (path, CARD_IMG_W, CARD_IMG_H)
            
            if key in self.product_display._img_cache:
                continue
            
            try:
                pil_img = Image.open(path).convert("RGB")
                iw, ih = pil_img.size
                scale = max(CARD_IMG_W / iw, CARD_IMG_H / ih)
                nw, nh = int(iw * scale), int(ih * scale)
                pil_img = pil_img.resize((nw, nh), Image.BILINEAR)
                left = (nw - CARD_IMG_W) // 2
                top = (nh - CARD_IMG_H) // 2
                pil_img = pil_img.crop((left, top, left + CARD_IMG_W, top + CARD_IMG_H))
                photo = ImageTk.PhotoImage(pil_img)
                self.product_display._img_cache[key] = photo
            except Exception as e:
                print(f"Failed to load {name}: {e}")
                self.product_display._img_cache[key] = None

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
        from logout_helper import logout_and_restart
        logout_and_restart(self.root)
    
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