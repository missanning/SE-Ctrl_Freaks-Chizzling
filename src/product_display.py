import tkinter as tk
import os
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

class ProductDisplay:
    def __init__(self, parent, pos_instance):
        self.parent = parent
        self.pos = pos_instance
        self.selected_product = None
        self.product_click_count = {}
        self.create_product_frame()
    
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
        
        filename = image_mapping.get(product_name, "no image.jpg")
        project_root = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(project_root, "assets", "food @chizzlin", filename)
    
    def create_product_frame(self):
        # Product List frame
        self.product_frame = tk.Frame(self.parent, bg="#FAF3E1", bd=1, relief="solid")
        self.product_frame.grid(row=1, column=0, rowspan=6, padx=10, pady=10, sticky="nsew")

        # Header with search
        header_frame = tk.Frame(self.product_frame, bg="#FAF3E1")
        header_frame.pack(fill="x", padx=5, pady=5)

        # Search bar
        search_frame = tk.Frame(header_frame, bg="#E9EAE2", bd=1, relief="flat")
        search_frame.pack(side="right", padx=10, pady=5)

        search_icon = tk.Label(search_frame, text="🔍", bg="#E9EAE2", font=("Arial", 10))
        search_icon.pack(side="right", padx=(6,2))

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

        # Product grid container
        canvas_frame = tk.Frame(self.product_frame, bg="#FAF3E1")
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
        
        # Mouse wheel scrolling
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
    
    def search_products(self, event=None):
        query = self.search_entry.get().lower()
        filtered = [p for p in self.pos.products if query in p[1].lower()]
        self.display_products(filtered)
    
    def display_products(self, products):
        # Clear existing widgets
        for widget in self.product_grid_frame.winfo_children():
            widget.destroy()
        
        # Display in 5-column grid
        cols = 5
        for i, product in enumerate(products):
            row = i // cols
            col = i % cols
            
            # Product frame
            product_item = tk.Frame(self.product_grid_frame, bg="#FFFFFF", bd=1, relief="solid", cursor="hand2")
            product_item.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Product image
            try:
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
            
            # Click handling
            def handle_product_click(prod=product, item_frame=product_item):
                prod_id = prod[0]
                if prod_id not in self.product_click_count:
                    self.product_click_count[prod_id] = 0
                
                self.product_click_count[prod_id] += 1
                
                # First click - select
                if self.product_click_count[prod_id] == 1:
                    self.selected_product = prod
                    # Clear highlights
                    for widget in self.product_grid_frame.winfo_children():
                        widget.config(bg="#FFFFFF")
                    # Highlight selected
                    item_frame.config(bg="#E6F3FF")
                    
                    # Reset after delay
                    self.parent.after(500, lambda: self.reset_click_count(prod_id))
                    
                # Second click - show dialog
                elif self.product_click_count[prod_id] == 2:
                    self.pos.show_quantity_dialog(prod)
                    self.product_click_count[prod_id] = 0
            
            # Bind events
            product_item.bind("<Button-1>", lambda e, prod=product: handle_product_click(prod, product_item))
            img_label.bind("<Button-1>", lambda e, prod=product: handle_product_click(prod, product_item))
            name_label.bind("<Button-1>", lambda e, prod=product: handle_product_click(prod, product_item))
            price_label.bind("<Button-1>", lambda e, prod=product: handle_product_click(prod, product_item))
        
        # Configure grid weights
        for col in range(cols):
            self.product_grid_frame.grid_columnconfigure(col, weight=1)
    
    def reset_click_count(self, prod_id):
        """Reset click count if no second click occurs"""
        if prod_id in self.product_click_count and self.product_click_count[prod_id] == 1:
            self.product_click_count[prod_id] = 0