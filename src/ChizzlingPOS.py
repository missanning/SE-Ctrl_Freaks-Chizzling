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
    return sqlite3.connect(db_path)

class ChizzlingPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Chizzling POS System")
        self.root.configure(bg="#FAF3E1")
        self.root.state("zoomed")
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(4, weight=1)
        
        # Initialize components
        self.products = []
        self.setup_components()
        self.root.update()
        self.load_products()
    
    def setup_components(self):
        """Initialize all POS components"""
        # Header
        self.header = POSHeader(self.root)
        
        # Product display
        self.product_display = ProductDisplay(self.root, self)
        
        # Category navigation
        self.category_nav = CategoryNavigation(self.root, self)
        
        # Cart manager
        self.cart_manager = CartManager(self.root, self)
    
    def load_products(self, category=None):
        """Load products from database"""
        conn = connect_db()
        cursor = conn.cursor()

        # Ensure category column exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]
        if "category" not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'All'")
            conn.commit()

        # Load products with category filter
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

        # Update product display
        self.product_display.display_products(self.products)
    
    def show_quantity_dialog(self, product):
        """Show quantity selection dialog"""
        QuantityDialog(self.root, product, self.cart_manager, self.product_display._img_cache)
    
    def cancel_order(self):
        """Cancel the current order"""
        self.cart_manager.cancel_order()
    
    def confirm_payment(self):
        """Process payment and complete transaction"""
        try:
            payment = float(self.cart_manager.payment_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid payment amount")
            return

        if payment < self.cart_manager.total:
            messagebox.showerror("Error", "Insufficient payment")
            return

        change = payment - self.cart_manager.total

        # Save transaction to database
        conn = connect_db()
        cursor = conn.cursor()

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
                       (self.cart_manager.total, payment, change, current_datetime))
        transaction_id = cursor.lastrowid

        # Save transaction items
        for item in self.cart_manager.cart:
            subtotal = item['price'] * item['qty']
            cursor.execute("""
                INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal)
                VALUES (?, ?, ?, ?)
            """, (transaction_id, item['id'], item['qty'], subtotal))

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", f"Transaction Saved! \nChange: ₱{change:.2f}")

        # Generate receipt
        cart_data = [(item['id'], item['name'], item['qty'], item['price'] * item['qty']) 
                     for item in self.cart_manager.cart]
        show_receipt_window(self.root, transaction_id, current_datetime, 
                          cart_data, self.cart_manager.total, change)

        # Clear cart
        self.cart_manager.clear_cart()

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = ChizzlingPOS(root)
    root.mainloop()

if __name__ == "__main__":
    main()