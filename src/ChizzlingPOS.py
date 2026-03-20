import tkinter as tk
from tkinter import messagebox
import sqlite3
from tkinter import PhotoImage
from tkinter import ttk
from receipt_module import show_receipt_window
import os

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
            text="⎋ EXIT",
            command=self.root.destroy,
            bg="#FF6600",
            fg="white",
            activebackground="#FF8844",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            width=10
        )
        logout_btn.place(relx=0.95, rely=0.5, anchor="e")

    def get_product_image_path(self, product_name):
        """Map product names to image filenames"""
        # Mapping of product names to image files
        image_mapping = {
            "Nachos": "nachos.jpg",
            "Shawarma Rice": "shawarmarice.jpg",
            "Fries - Cheese": "fries.jpg",
            "Fries - Barbeque": "fries.jpg",
            "Fries - Sour and Cream": "fries.jpg",
            "Takoyaki - Cheese (5pcs)": "takoyakicheese.jpg",
            "Takoyaki - Ham and Cheese (5pcs)": "takoyakihamcheese.jpg",
            "Takoyaki - Crab (5pcs)": "takoyakicrab.jpg",
            "Takoyaki - Overload (7pcs)": "takoyakioverload.jpg",
            "Chicken Tenders": "chickentenderscheese.jpg",
            "Sisig Silog": "sisigsilog.jpg",
            "Chicken silog": "chicksilog.jpg",
            "Sizzling Sisig (Rice Meal)": "sizzlingsisig.jpg",
            "Sizzling Tofu (Rice Meal)": "sizzlingtofu.png",
            "Sizzling Liempo (Rice Meal)": "sizzlingliempo.jpg",
            "Sizzling Sisig": "sizzlingsisig.jpg",
            "Sizzling Tofu": "sizzlingtofu.png",
            "Sizzling Liempo": "sizzlingliempo.jpg",
            "Sisig and Liempo": "sisig_liempo.png",
            "Sisig and Tofu": "tofu_sisig.png",
            "Sizzling Liempo and Tofu": "liempo_tofu.png",
            "Red Horse 1 Litro": "redhorse.jpg",
            "Alfonso Light": "alfonsolight.jpg",
            "Gin Bilog": "ginbilog.jpg",
            "Gin Kwatro": "ginkwatro.jpg",
            "Pale Pilsen": "redhorse.jpg"
        }
        
        filename = image_mapping.get(product_name, "no image.jpg")
        project_root = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(project_root, "assets", "food @chizzlin", filename)

    def search_products(self, event=None):
        query = self.search_entry.get().lower()
        filtered = [p for p in self.products if query in p[1].lower()]
        self.display_products(filtered)


    def create_widgets(self):
        # Product List (left)
        product_frame = tk.Frame(self.root, bg="#FAF3E1", bd=1, relief="solid")
        product_frame.grid(row=1, column=0, rowspan=6, padx=10, pady=10, sticky="nsew")

        # --- Header inside product frame ---
        header_frame = tk.Frame(product_frame, bg="#FAF3E1")
        header_frame.pack(fill="x", padx=5, pady=5)

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

        # --- Product Grid Container ---
        canvas_frame = tk.Frame(product_frame, bg="#FAF3E1")
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=(0,5))
        
        self.product_canvas = tk.Canvas(canvas_frame, bg="#FAF3E1", highlightthickness=0)
        product_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.product_canvas.yview)
        self.product_grid_frame = tk.Frame(self.product_canvas, bg="#FAF3E1")
        
        self.product_grid_frame.bind(
            "<Configure>",
            lambda e: self.product_canvas.configure(scrollregion=self.product_canvas.bbox("all"))
        )
        
        self.product_canvas.create_window((0, 0), window=self.product_grid_frame, anchor="nw")
        self.product_canvas.configure(yscrollcommand=product_scrollbar.set)
        
        # Mouse wheel scrolling for products
        def _on_product_mousewheel(event):
            if self.product_canvas.bbox("all"):
                bbox = self.product_canvas.bbox("all")
                canvas_height = self.product_canvas.winfo_height()
                if bbox[3] > canvas_height:
                    self.product_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_product_mousewheel(event):
            self.product_canvas.bind_all("<MouseWheel>", _on_product_mousewheel)
        
        def _unbind_product_mousewheel(event):
            self.product_canvas.unbind_all("<MouseWheel>")
        
        self.product_canvas.bind("<Enter>", _bind_product_mousewheel)
        self.product_canvas.bind("<Leave>", _unbind_product_mousewheel)
        
        self.product_canvas.pack(side="left", fill="both", expand=True)
        product_scrollbar.pack(side="right", fill="y")

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

        # Store selected product and click tracking
        self.selected_product = None
        self.product_click_count = {}

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
        
        # Enable mouse wheel scrolling only when hovering over cart canvas
        def _on_mousewheel(event):
            # Only scroll if content is larger than visible area
            if self.cart_canvas.bbox("all"):
                bbox = self.cart_canvas.bbox("all")
                canvas_height = self.cart_canvas.winfo_height()
                if bbox[3] > canvas_height:
                    self.cart_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            self.cart_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            self.cart_canvas.unbind_all("<MouseWheel>")
        
        self.cart_canvas.bind("<Enter>", _bind_mousewheel)
        self.cart_canvas.bind("<Leave>", _unbind_mousewheel)
        
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
        # Clear existing product widgets
        for widget in self.product_grid_frame.winfo_children():
            widget.destroy()
        
        # Display products in a grid with images
        cols = 5
        for i, product in enumerate(products):
            row = i // cols
            col = i % cols
            
            # Create product frame
            product_item = tk.Frame(self.product_grid_frame, bg="#FFFFFF", bd=1, relief="solid", cursor="hand2")
            product_item.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            try:
                # Load and resize product image (bigger size)
                if Image and ImageTk:
                    img_path = self.get_product_image_path(product[1])
                    if os.path.exists(img_path):
                        pil_img = Image.open(img_path)
                        pil_img = pil_img.resize((195, 180), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(pil_img)
                    else:
                        pil_img = Image.new('RGB', (195, 180), color='lightgray')
                        photo = ImageTk.PhotoImage(pil_img)
                else:
                    photo = None
                
                if photo:
                    img_label = tk.Label(product_item, image=photo, bg="#FFFFFF")
                    img_label.image = photo
                    img_label.pack(pady=5)
                else:
                    img_label = tk.Label(product_item, text="[IMG]", bg="#FFFFFF", width=24, height=15)
                    img_label.pack(pady=5)
                    
            except Exception:
                img_label = tk.Label(product_item, text="[IMG]", bg="#FFFFFF", width=24, height=15)
                img_label.pack(pady=5)
            
            # Product name
            name_label = tk.Label(product_item, text=product[1], bg="#FFFFFF", 
                                font=("Arial", 8), wraplength=195, justify="center")
            name_label.pack(pady=(0,5))
            
            # Price
            price_label = tk.Label(product_item, text=f"₱{product[2]:.2f}", bg="#FFFFFF", 
                                 font=("Arial", 8, "bold"), fg="#FF6600")
            price_label.pack(pady=(0,5))
            
            # Bind click events to select product with double-click detection
            def handle_product_click(prod=product, item_frame=product_item):
                # Track clicks for this product
                prod_id = prod[0]
                if prod_id not in self.product_click_count:
                    self.product_click_count[prod_id] = 0
                
                self.product_click_count[prod_id] += 1
                
                # First click - select product
                if self.product_click_count[prod_id] == 1:
                    self.selected_product = prod
                    # Clear all highlights
                    for widget in self.product_grid_frame.winfo_children():
                        widget.config(bg="#FFFFFF")
                    # Highlight selected
                    item_frame.config(bg="#E6F3FF")
                    
                    # Reset click count after delay if no second click
                    self.root.after(500, lambda: self.reset_click_count(prod_id))
                    
                # Second click - show quantity dialog
                elif self.product_click_count[prod_id] == 2:
                    self.show_quantity_dialog(prod)
                    self.product_click_count[prod_id] = 0  # Reset
            
            product_item.bind("<Button-1>", lambda e, prod=product: handle_product_click(prod, product_item))
            img_label.bind("<Button-1>", lambda e, prod=product: handle_product_click(prod, product_item))
            name_label.bind("<Button-1>", lambda e, prod=product: handle_product_click(prod, product_item))
            price_label.bind("<Button-1>", lambda e, prod=product: handle_product_click(prod, product_item))
        
        # Configure grid weights
        for col in range(cols):
            self.product_grid_frame.grid_columnconfigure(col, weight=1)

    def reset_click_count(self, prod_id):
        """Reset click count if no second click occurs within time limit"""
        if prod_id in self.product_click_count and self.product_click_count[prod_id] == 1:
            self.product_click_count[prod_id] = 0
    
    def show_quantity_dialog(self, product):
        """Show dialog with product image and quantity selection"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add to Cart")
        dialog.geometry("400x500")
        dialog.configure(bg="#FFFFFF")
        dialog.resizable(False, False)
        
        # Center the dialog on screen
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Calculate center position
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Product image
        try:
            if Image and ImageTk:
                img_path = self.get_product_image_path(product[1])
                if os.path.exists(img_path):
                    pil_img = Image.open(img_path)
                    pil_img = pil_img.resize((200, 150), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(pil_img)
                    img_label = tk.Label(dialog, image=photo, bg="#FFFFFF")
                    img_label.image = photo
                    img_label.pack(pady=20)
                else:
                    tk.Label(dialog, text="[No Image]", bg="#FFFFFF", width=25, height=10).pack(pady=20)
            else:
                tk.Label(dialog, text="[No Image]", bg="#FFFFFF", width=25, height=10).pack(pady=20)
        except Exception:
            tk.Label(dialog, text="[No Image]", bg="#FFFFFF", width=25, height=10).pack(pady=20)
        
        # Product name
        tk.Label(dialog, text=product[1], bg="#FFFFFF", font=("Arial", 12, "bold"), 
                wraplength=350, justify="center").pack(pady=10)
        
        # Price
        tk.Label(dialog, text=f"₱{product[2]:.2f}", bg="#FFFFFF", 
                font=("Arial", 11, "bold"), fg="#FF6600").pack(pady=5)
        
        # Quantity frame
        qty_frame = tk.Frame(dialog, bg="#FFFFFF")
        qty_frame.pack(pady=20)
        
        tk.Label(qty_frame, text="Quantity:", bg="#FFFFFF", font=("Arial", 10)).pack(side="left", padx=5)
        
        # Quantity controls
        qty_var = tk.IntVar(value=1)
        
        def decrease_qty():
            if qty_var.get() > 1:
                qty_var.set(qty_var.get() - 1)
        
        def increase_qty():
            qty_var.set(qty_var.get() + 1)
        
        tk.Button(qty_frame, text="-", command=decrease_qty, width=3).pack(side="left", padx=2)
        qty_label = tk.Label(qty_frame, textvariable=qty_var, bg="#FFFFFF", width=5, 
                           font=("Arial", 10), relief="sunken")
        qty_label.pack(side="left", padx=5)
        tk.Button(qty_frame, text="+", command=increase_qty, width=3).pack(side="left", padx=2)
        
        # Buttons frame
        btn_frame = tk.Frame(dialog, bg="#FFFFFF")
        btn_frame.pack(pady=30)
        
        # Add to Cart button
        def add_to_cart_from_dialog():
            qty = qty_var.get()
            # Check if product already in cart
            for item in self.cart:
                if item['id'] == product[0]:
                    item['qty'] += qty
                    self.update_cart()
                    dialog.destroy()
                    return
            
            # Add new product to cart
            self.cart.append({'id': product[0], 'name': product[1], 'price': product[2], 'qty': qty})
            self.update_cart()
            self.update_total()
            dialog.destroy()
        
        tk.Button(btn_frame, text="Add to Cart", command=add_to_cart_from_dialog,
                 bg="#FF6600", fg="white", activebackground="#FF8844", activeforeground="white",
                 relief="raised", width=12, font=("Arial", 10)).pack(side="left", padx=10)
        
        # Cancel button
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg="#DC3545", fg="white", activebackground="#C82333", activeforeground="white",
                 relief="raised", width=12, font=("Arial", 10)).pack(side="left", padx=10)

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

        from datetime import datetime
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
                       (self.total, payment, change, current_datetime))
        transaction_id = cursor.lastrowid

        for item in self.cart:
            subtotal = item['price'] * item['qty']
            cursor.execute("""
                INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal)
                VALUES (?, ?, ?, ?)
            """, (transaction_id, item['id'], item['qty'], subtotal))

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", f"Transaction Saved!\nChange: {change:.2f}")

        # Generate receipt
        cart_data = [(item['id'], item['name'], item['qty'], item['price'] * item['qty']) for item in self.cart]
        show_receipt_window(self.root, transaction_id, current_datetime, cart_data, self.total, change)

        # Reset cart
        self.cart = []
        self.update_cart()
        self.payment_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = POS(root)
    root.mainloop()
