import tkinter as tk
from tkinter import messagebox
import sqlite3
from tkinter import PhotoImage
from tkinter import ttk

# For responsive image scaling (optional; falls back to Tkinter PhotoImage if missing)
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

# Connect to database
def connect_db():
    import os
    db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
    return sqlite3.connect(db_path)

def get_asset_path(filename):
    import os
    # Get the parent directory of src (project root)
    project_root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_root, "assets", filename)

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Chizzling POS")
        self.root.geometry("300x150")
        
        tk.Label(root, text="Username:").grid(row=0, column=0, padx=10, pady=10)
        self.username_entry = tk.Entry(root)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(root, text="Password:").grid(row=1, column=0, padx=10, pady=10)
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        tk.Button(root, text="Login", command=self.login).grid(row=2, column=0, columnspan=2, pady=10)
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.root.destroy()
            root = tk.Tk()
            app = POS(root)
            root.mainloop()
        else:
            messagebox.showerror("Error", "Invalid credentials")

class POS:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales and Inventory POS System")
        self.root.configure(bg="#FAF3E1")

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(4, weight=1)

        self.root.state("zoomed")
        
        self.cart = []
        self.total = 0

        self.create_header()
        self.create_widgets()
        self.load_products()
        
    def create_header(self):

        # Shadow frame
        shadow = tk.Frame(self.root, bg="#423e3e")
        shadow.grid(row=0, column=0, columnspan=3, sticky="ew", padx=3, pady=(3,0))

        # Actual header frame
        header = tk.Frame(self.root)
        header.grid(row=0, column=0, columnspan=3, sticky="nsew")
        header.grid_propagate(False)

        # Load header image. Use PIL (ImageTk) if available so the image can scale to fill the header.
        if Image is not None and ImageTk is not None:
            self.header_pil = Image.open(get_asset_path("HEADER.png"))
            self.header_img = ImageTk.PhotoImage(self.header_pil)

            header_label = tk.Label(header, image=self.header_img, borderwidth=0, relief="flat")
            header_label.pack(fill="x", expand=True)

            def _resize_header(event):
                if event.width <= 1 or event.height <= 1:
                    return
                resized = self.header_pil.resize((event.width, event.height), Image.LANCZOS)
                self.header_img = ImageTk.PhotoImage(resized)
                header_label.config(image=self.header_img)
                header_label.image = self.header_img

            header.bind("<Configure>", _resize_header)
        else:
            # Fall back to Tkinter PhotoImage (fixed size)
            self.header_img = tk.PhotoImage(file=get_asset_path("HEADER.png"))
            header_label = tk.Label(header, image=self.header_img, borderwidth=0, relief="solid")
            header_label.pack(fill="both", expand=True)
            
    
        # Logout button on top of image (orange)
        logout_btn = tk.Button(
            header_label,
            text="⎋ LOGOUT",
            command=self.logout,
            bg="#FF6600",
            fg="white",
            activebackground="#FF8844",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            width=10
        )
        logout_btn.place(relx=0.95, rely=0.5, anchor="e")

    def search_products(self, event=None):
        query = self.search_entry.get().lower()

        filtered = [p for p in self.products if query in p[1].lower()]

        self.product_listbox.delete(0, tk.END)

        for product in filtered:
            self.product_listbox.insert(tk.END, f"{product[1]} - {product[2]}")

    def add_new_item(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New Product")
        add_window.geometry("300x250")

        tk.Label(add_window, text="Product Name").pack()
        name_entry = tk.Entry(add_window)
        name_entry.pack()

        tk.Label(add_window, text="Price").pack()
        price_entry = tk.Entry(add_window)
        price_entry.pack()

        tk.Label(add_window, text="Category").pack()
        category_entry = tk.Entry(add_window)
        category_entry.pack()

        tk.Label(add_window, text="Stock").pack()
        stock_entry = tk.Entry(add_window)
        stock_entry.pack()

        def save_product():
            name = name_entry.get()
            price = price_entry.get()
            category = category_entry.get()
            stock = stock_entry.get()

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO products (name, price, category, stock) VALUES (?, ?, ?, ?)",
                (name, price, category, stock)
            )

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Product added successfully")

            add_window.destroy()

            # reload product list
            self.product_listbox.delete(0, tk.END)
            self.load_products()

        tk.Button(add_window, text="Save Product", command=save_product).pack(pady=10)
        
    def create_widgets(self):
        # Product List (left)
        product_frame = tk.Frame(self.root, bg="#FAF3E1", bd=1, relief="solid")
        product_frame.grid(row=1, column=0, rowspan=6, padx=10, pady=10, sticky="nsew")

        # --- Header inside product frame ---
        header_frame = tk.Frame(product_frame, bg="#FAF3E1")
        header_frame.pack(fill="x", padx=5, pady=5)

        # Add New Item (clickable)
        add_item_label = tk.Label(
            header_frame,
            text="➕ Add New Item",
            fg="#333333",  
            cursor="hand2",
            bg="#FAF3E1",
            font=("Arial", 10, "underline")
        )
        add_item_label.pack(side="left")
        add_item_label.bind("<Button-1>", lambda e: self.add_new_item())
        add_item_label.bind("<Enter>", lambda e: add_item_label.config(fg="#FF8C00"))
        add_item_label.bind("<Leave>", lambda e: add_item_label.config(fg="#333333"))

        # Search bar container
        search_frame = tk.Frame(header_frame, bg="#E9EAE2", bd=1, relief="flat")
        search_frame.pack(side="right", padx=10, pady=5)

        # Search icon
        search_icon = tk.Label(search_frame, text="🔍", bg="#E9EAE2", font=("Arial", 10))
        search_icon.pack(side="right", padx=(6,2))

        # Search entry
        self.search_entry = tk.Entry(
            search_frame,
            width=23,
            bd=0,
            font=("Arial", 10),
            bg="#E9EAE2",
            insertbackground="black"
        )
        self.search_entry.pack(side="left", padx=(0,6), pady=4)

        self.search_entry.bind("<KeyRelease>", self.search_products)

        # --- Actual Listbox below header ---
        self.product_listbox = tk.Listbox(product_frame, width=40)
        self.product_listbox.pack(fill="both", expand=True, padx=5, pady=(0,5))

        # Add to Cart button (placed inside product panel so it stays visible)
        # Add to Cart button (orange)
        tk.Button(product_frame, text="Add to Cart", command=self.add_to_cart,
                  bg="#FF6600", fg="white", activebackground="#FF8844", activeforeground="white",
                  relief="raised").pack(fill="x", padx=10, pady=(0, 10))

        # --- Load images --- NOT YET ACTIVATED DUE TO THE DATABASE NOT HAVINF CATEGORY FIELD YET
        self.meals_img_inactive = tk.PhotoImage(file=get_asset_path("MEALS1.png"))
        self.snacks_img_inactive = tk.PhotoImage(file=get_asset_path("SNACKS1.png"))
        self.drinks_img_inactive = tk.PhotoImage(file=get_asset_path("DRINKS1.png"))
        self.alcohol_img_inactive = tk.PhotoImage(file=get_asset_path("ALCOHOL1.png"))
        self.all_img_inactive = tk.PhotoImage(file=get_asset_path("ALL1.png"))

        self.meals_img_active = tk.PhotoImage(file=get_asset_path("MEALS.png"))
        self.snacks_img_active = tk.PhotoImage(file=get_asset_path("SNACKS.png"))
        self.drinks_img_active = tk.PhotoImage(file=get_asset_path("DRINKS.png"))
        self.alcohol_img_active = tk.PhotoImage(file=get_asset_path("ALCOHOL.png"))
        self.all_img_active = tk.PhotoImage(file=get_asset_path("ALL.png"))

        # --- Category Frame ---
        category_frame = tk.Frame(self.root, bg="#FAF3E1")
        category_frame.grid(row=7, column=0, padx=10, pady=10, sticky="ew")

        # --- Create label references ---
        self.category_labels = {}

        # Helper function to set active image
        def set_active_category(category):
            category = category.lower()
            self.current_category = category
            for cat, label in self.category_labels.items():
                if cat == category:
                    label.config(image=getattr(self, f"{cat}_img_active"))
                else:
                    label.config(image=getattr(self, f"{cat}_img_inactive"))

            if category == "all":
                self.load_products(None)
            else:
                self.load_products(category)

        # --- Meals ---
        meals_label = tk.Label(category_frame, image=self.meals_img_active, cursor="hand2", bg="#FAF3E1")
        meals_label.grid(row=0, column=0, padx=5)
        meals_label.bind("<Button-1>", lambda e: set_active_category("meals"))
        self.category_labels["meals"] = meals_label

        # --- Snacks ---
        snacks_label = tk.Label(category_frame, image=self.snacks_img_inactive, cursor="hand2", bg="#FAF3E1")
        snacks_label.grid(row=0, column=1, padx=5)
        snacks_label.bind("<Button-1>", lambda e: set_active_category("snacks"))
        self.category_labels["snacks"] = snacks_label

        # --- Drinks ---
        drinks_label = tk.Label(category_frame, image=self.drinks_img_inactive, cursor="hand2", bg="#FAF3E1")
        drinks_label.grid(row=0, column=2, padx=5)
        drinks_label.bind("<Button-1>", lambda e: set_active_category("drinks"))
        self.category_labels["drinks"] = drinks_label

        # --- Alcohol ---
        alcohol_label = tk.Label(category_frame, image=self.alcohol_img_inactive, cursor="hand2", bg="#FAF3E1")
        alcohol_label.grid(row=0, column=3, padx=5)
        alcohol_label.bind("<Button-1>", lambda e: set_active_category("alcohol"))
        self.category_labels["alcohol"] = alcohol_label

        # --- All ---
        all_label = tk.Label(category_frame, image=self.all_img_inactive, cursor="hand2", bg="#FAF3E1")
        all_label.grid(row=0, column=4, padx=5)
        all_label.bind("<Button-1>", lambda e: set_active_category("all"))
        self.category_labels["all"] = all_label

        # --- Cancel Button ---
        cancel_btn = tk.Button(
            category_frame,
            text="CANCEL ORDER",
            command=self.cancel_order,
            bg="#DC3545",
            fg="white",
            activebackground="#C82333",
            activeforeground="white",
            relief="raised",
            cursor="hand2",
            width=15
        )
        cancel_btn.grid(row=0, column=5, padx=10)

        # Default to showing all products
        set_active_category("all")

        # --- Checkout Frame ---
        self.cart_frame = tk.Frame(self.root, bg="#FFFFFF", bd=2, relief="raised")
        self.cart_frame.grid(row=1, column=2, rowspan=7, padx=5, pady=10, sticky="ns")
        self.cart_frame.grid_propagate(False)
        # Wider checkout panel to accommodate longer item names and totals
        self.cart_frame.configure(width=720, height=550)

        # Make frame expand vertically (fixed width)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=0)

        # Title
        tk.Label(self.cart_frame, text="CHECKOUT LIST", font=("Arial", 10, "bold"),
                bg="#FFFFFF").grid(row=0, column=0, columnspan=3, padx=100, pady=5, sticky="ew")

        # Create a canvas with scrollbar for cart items
        canvas_container = tk.Frame(self.cart_frame, bg="#FFFFFF")
        canvas_container.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=10, pady=(0, 5))
        
        self.cart_canvas = tk.Canvas(canvas_container, bg="#FFFFFF", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=self.cart_canvas.yview)
        self.cart_items_frame = tk.Frame(self.cart_canvas, bg="#FFFFFF")
        
        self.cart_items_frame.bind(
            "<Configure>",
            lambda e: self.cart_canvas.configure(scrollregion=self.cart_canvas.bbox("all"))
        )
        
        self.cart_canvas.create_window((0, 0), window=self.cart_items_frame, anchor="nw")
        self.cart_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            self.cart_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.cart_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self.cart_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Make the item rows align with the header columns
        for col, weight in enumerate((4, 1, 1, 1, 2)):
            self.cart_items_frame.grid_columnconfigure(col, weight=weight)

        # Header row (same grid so it aligns with data rows)
        header_bg = "#FFFFFF"
        tk.Label(self.cart_items_frame, text="Name", bg=header_bg, width=18).grid(row=0, column=0, sticky="w", padx=10)
        tk.Label(self.cart_items_frame, text="", bg=header_bg, width=2).grid(row=0, column=1)
        tk.Label(self.cart_items_frame, text="QTY", bg=header_bg, width=6).grid(row=0, column=2)
        tk.Label(self.cart_items_frame, text="", bg=header_bg, width=2).grid(row=0, column=3)
        tk.Label(self.cart_items_frame, text="PRICE", bg=header_bg, width=8).grid(row=0, column=4, sticky="e", padx=10)

        self.cart = []

        # Allow the cart list to expand
        self.cart_frame.grid_rowconfigure(1, weight=1)
        self.cart_frame.grid_columnconfigure(0, weight=1)

        # Total + payment
        self.total_label = tk.Label(self.cart_frame, text="Total: 0", bg="#FFFFFF", font=("Arial", 10, "bold"))
        self.total_label.grid(row=2, column=0, columnspan=3, pady=(10, 5), sticky="w", padx=10)

        tk.Label(self.cart_frame, text="Payment:", bg="#FFFFFF").grid(row=4, column=0, sticky="w", padx=10)
        self.payment_entry = tk.Entry(self.cart_frame)
        self.payment_entry.grid(row=4, column=1, columnspan=2, pady=5, sticky="ew", padx=10)

        tk.Button(self.cart_frame, text="Confirm Payment", command=self.confirm_payment,
                  bg="#28A745", fg="white", activebackground="#3DC06B", activeforeground="white",
                  relief="raised").grid(row=5, column=0, columnspan=3, pady=10, padx=10, sticky="ew")
    
    def logout(self):
        self.root.destroy()
        root = tk.Tk()
        app = LoginWindow(root)
        root.mainloop()

    def cancel_order(self):
        if not self.cart:
            messagebox.showinfo("Info", "Cart is already empty")
            return
        
        response = messagebox.askyesno("Cancel Order", "Are you sure you want to cancel all items in the cart?")
        if response:
            self.cart = []
            self.update_cart()
            self.payment_entry.delete(0, tk.END)
            messagebox.showinfo("Success", "All items have been removed from cart")

    def load_products(self, category=None):
        conn = connect_db()
        cursor = conn.cursor()

        # Ensure the products table has a category column (for legacy DBs)
        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]
        if "category" not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'All'")
            conn.commit()

        # Load products (filter by category if provided)
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

        self.display_products(self.products)

    def display_products(self, products):
        self.product_listbox.delete(0, tk.END)
        for product in products:
            self.product_listbox.insert(tk.END, f"{product[1]} - {product[2]:.2f}")

    def add_to_cart(self):
        selected = self.product_listbox.curselection()
        if not selected:
            return

        index = selected[0]
        product = self.products[index]

        qty = 1

        # Check if product already in cart
        for item in self.cart:
            if item['id'] == product[0]:
                item['qty'] += qty
                self.update_cart()
                return

        # Add new product to cart
        self.cart.append({'id': product[0], 'name': product[1], 'price': product[2], 'qty': qty})
        self.update_cart()
        self.update_total()

    def update_cart(self):
        # Clear current rows (including header), then rebuild header + items so the header never disappears.
        for widget in self.cart_items_frame.winfo_children():
            widget.destroy()

        # Header row (kept in sync with item columns)
        header_bg = "#FFFFFF"
        tk.Label(self.cart_items_frame, text="Name", bg=header_bg, width=18).grid(row=0, column=0, sticky="w", padx=10)
        tk.Label(self.cart_items_frame, text="", bg=header_bg, width=2).grid(row=0, column=1)
        tk.Label(self.cart_items_frame, text="QTY", bg=header_bg, width=6).grid(row=0, column=2)
        tk.Label(self.cart_items_frame, text="", bg=header_bg, width=2).grid(row=0, column=3)
        tk.Label(self.cart_items_frame, text="PRICE", bg=header_bg, width=8).grid(row=0, column=4, sticky="e", padx=10)

        for i, item in enumerate(self.cart):
            row = i + 1  # offset by 1 because row 0 is header

            name = item['name']
            qty = item['qty']
            price = item['price'] * qty

            # Name
            tk.Label(self.cart_items_frame, text=name, bg="#FFFFFF").grid(row=row, column=0, padx=(10,4), pady=2, sticky="w")

            # Minus button
            tk.Button(self.cart_items_frame, text="-", width=2,
                    command=lambda x=i: self.change_qty(x,-1)).grid(row=row, column=1, padx=2, pady=2)

            # Quantity
            tk.Label(self.cart_items_frame, text=str(qty), width=6,
                    bg="#FFFFFF").grid(row=row, column=2, padx=2, pady=2)

            # Plus button
            tk.Button(self.cart_items_frame, text="+", width=2,
                    command=lambda x=i: self.change_qty(x,1)).grid(row=row, column=3, padx=2, pady=2)

            # Price
            tk.Label(self.cart_items_frame, text=f"{price:.2f}", width=8, 
                    bg="#FFFFFF").grid(row=row, column=4, padx=(4,10), pady=2, sticky="e")
        
        # Update total whenever cart changes
        self.update_total()

    def change_qty(self, index, delta):
        self.cart[index]['qty'] += delta

        if self.cart[index]['qty'] <= 0:
            self.cart.pop(index)

        self.update_cart()
        self.update_total()

    def update_total(self):
        self.total = sum(item['price'] * item['qty'] for item in self.cart)
        self.total_label.config(text=f"Total: {self.total:.2f}")

    def confirm_payment(self):
        try:
            payment = float(self.payment_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid payment")
            return

        if payment < self.total:
            messagebox.showerror("Error", "Insufficient payment")
            return

        change = payment - self.total

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO transactions (total, payment, change) VALUES (?, ?, ?)",
                       (self.total, payment, change))
        transaction_id = cursor.lastrowid

        for item in self.cart:
            subtotal = item['price'] * item['qty']
            cursor.execute("""
                INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal)
                VALUES (?, ?, ?, ?)
            """, (transaction_id, item['id'], item['qty'], subtotal))

            cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                           (item['qty'], item['id']))

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", f"Transaction Saved!\nChange: {change:.2f}")

        # Reset cart
        self.cart = []
        self.update_cart()
        self.payment_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()
