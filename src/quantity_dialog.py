import tkinter as tk
import os
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

class QuantityDialog:
    def __init__(self, parent, product, cart_manager):
        self.parent = parent
        self.product = product
        self.cart_manager = cart_manager
        self.show_dialog()
    
    def get_product_image_path(self, product_name):
        """Map product names to image filenames"""
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
        
        filename = image_mapping.get(product_name, "nachos.jpg")
        project_root = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(project_root, "assets", "food @chizzlin", filename)
    
    def show_dialog(self):
        """Show the quantity selection dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add to Cart")
        self.dialog.geometry("400x500")
        self.dialog.configure(bg="#FFFFFF")
        self.dialog.resizable(False, False)
        
        # Center the dialog on screen
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Calculate center position
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Product image
        self.create_product_image()
        
        # Product details
        self.create_product_details()
        
        # Quantity controls
        self.create_quantity_controls()
        
        # Action buttons
        self.create_action_buttons()
    
    def create_product_image(self):
        """Create the product image display"""
        try:
            if Image and ImageTk:
                img_path = self.get_product_image_path(self.product[1])
                if os.path.exists(img_path):
                    pil_img = Image.open(img_path)
                    pil_img = pil_img.resize((200, 150), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(pil_img)
                    img_label = tk.Label(self.dialog, image=photo, bg="#FFFFFF")
                    img_label.image = photo
                    img_label.pack(pady=20)
                else:
                    tk.Label(self.dialog, text="[No Image]", bg="#FFFFFF", width=25, height=10).pack(pady=20)
            else:
                tk.Label(self.dialog, text="[No Image]", bg="#FFFFFF", width=25, height=10).pack(pady=20)
        except Exception:
            tk.Label(self.dialog, text="[No Image]", bg="#FFFFFF", width=25, height=10).pack(pady=20)
    
    def create_product_details(self):
        """Create product name and price display"""
        # Product name
        tk.Label(self.dialog, text=self.product[1], bg="#FFFFFF", font=("Arial", 12, "bold"), 
                wraplength=350, justify="center").pack(pady=10)
        
        # Price
        tk.Label(self.dialog, text=f"₱{self.product[2]:.2f}", bg="#FFFFFF", 
                font=("Arial", 11, "bold"), fg="#FF6600").pack(pady=5)
    
    def create_quantity_controls(self):
        """Create quantity selection controls"""
        qty_frame = tk.Frame(self.dialog, bg="#FFFFFF")
        qty_frame.pack(pady=20)
        
        tk.Label(qty_frame, text="Quantity:", bg="#FFFFFF", font=("Arial", 10)).pack(side="left", padx=5)
        
        # Quantity variable
        self.qty_var = tk.IntVar(value=1)
        
        def decrease_qty():
            if self.qty_var.get() > 1:
                self.qty_var.set(self.qty_var.get() - 1)
        
        def increase_qty():
            self.qty_var.set(self.qty_var.get() + 1)
        
        # Quantity controls
        tk.Button(qty_frame, text="-", command=decrease_qty, width=3).pack(side="left", padx=2)
        qty_label = tk.Label(qty_frame, textvariable=self.qty_var, bg="#FFFFFF", width=5, 
                           font=("Arial", 10), relief="sunken")
        qty_label.pack(side="left", padx=5)
        tk.Button(qty_frame, text="+", command=increase_qty, width=3).pack(side="left", padx=2)
    
    def create_action_buttons(self):
        """Create Add to Cart and Cancel buttons"""
        btn_frame = tk.Frame(self.dialog, bg="#FFFFFF")
        btn_frame.pack(pady=30)
        
        # Add to Cart button
        tk.Button(btn_frame, text="Add to Cart", command=self.add_to_cart,
                 bg="#FF6600", fg="white", activebackground="#FF8844", activeforeground="white",
                 relief="raised", width=12, font=("Arial", 10)).pack(side="left", padx=10)
        
        # Cancel button
        tk.Button(btn_frame, text="Cancel", command=self.dialog.destroy,
                 bg="#DC3545", fg="white", activebackground="#C82333", activeforeground="white",
                 relief="raised", width=12, font=("Arial", 10)).pack(side="left", padx=10)
    
    def add_to_cart(self):
        """Add the product to cart with selected quantity"""
        qty = self.qty_var.get()
        self.cart_manager.add_item(self.product[0], self.product[1], self.product[2], qty)
        self.dialog.destroy()