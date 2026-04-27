import tkinter as tk
import os

def get_asset_path(filename):
    """Get the full path to an asset file"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_root, "assets", filename)

class CategoryNavigation:
    def __init__(self, parent, pos_instance):
        self.parent = parent
        self.pos = pos_instance
        self.category_labels = {}
        self.current_category = "meals"
        self.load_category_images()
        self.create_category_frame()
    
    def load_category_images(self):
        """Load all category images"""
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
    
    def create_category_frame(self):
        """Create the category navigation frame"""
        category_frame = tk.Frame(self.parent, bg="#FAF3E1")
        category_frame.grid(row=7, column=0, padx=10, pady=10, sticky="ew")

        # Meals
        meals_label = tk.Label(category_frame, image=self.meals_img_active, cursor="hand2", bg="#FAF3E1")
        meals_label.grid(row=0, column=0, padx=5)
        meals_label.bind("<Button-1>", lambda e: self.set_active_category("meals"))
        self.category_labels["meals"] = meals_label

        # Snacks
        snacks_label = tk.Label(category_frame, image=self.snacks_img_inactive, cursor="hand2", bg="#FAF3E1")
        snacks_label.grid(row=0, column=1, padx=5)
        snacks_label.bind("<Button-1>", lambda e: self.set_active_category("snacks"))
        self.category_labels["snacks"] = snacks_label

        # Drinks
        drinks_label = tk.Label(category_frame, image=self.drinks_img_inactive, cursor="hand2", bg="#FAF3E1")
        drinks_label.grid(row=0, column=2, padx=5)
        drinks_label.bind("<Button-1>", lambda e: self.set_active_category("drinks"))
        self.category_labels["drinks"] = drinks_label

        # Alcohol
        alcohol_label = tk.Label(category_frame, image=self.alcohol_img_inactive, cursor="hand2", bg="#FAF3E1")
        alcohol_label.grid(row=0, column=3, padx=5)
        alcohol_label.bind("<Button-1>", lambda e: self.set_active_category("alcohol"))
        self.category_labels["alcohol"] = alcohol_label

        # All
        all_label = tk.Label(category_frame, image=self.all_img_inactive, cursor="hand2", bg="#FAF3E1")
        all_label.grid(row=0, column=4, padx=5)
        all_label.bind("<Button-1>", lambda e: self.set_active_category("all"))
        self.category_labels["all"] = all_label

        # Cancel Order button
        cancel_btn = tk.Button(
            category_frame,
            text="CANCEL ORDER",
            command=self.pos.cancel_order,
            bg="#DC3545",
            fg="white",
            activebackground="#C82333",
            activeforeground="white",
            relief="raised",
            cursor="hand2",
            font=("Arial", 12, "bold"),
            width=18,
            height=2,
            bd=3
        )
        cancel_btn.grid(row=0, column=5, padx=10, pady=5)

        # Set default category without triggering load (load is deferred in ChizzlingPOS)
        self.current_category = "all"
        for cat, label in self.category_labels.items():
            if cat == "all":
                label.config(image=self.all_img_active)
            else:
                label.config(image=getattr(self, f"{cat}_img_inactive"))
    
    def set_active_category(self, category):
        """Set the active category and update display"""
        category = category.lower()
        self.current_category = category
        
        # Update category button images
        for cat, label in self.category_labels.items():
            if cat == category:
                label.config(image=getattr(self, f"{cat}_img_active"))
            else:
                label.config(image=getattr(self, f"{cat}_img_inactive"))

        # Load products for category
        if category == "all":
            self.pos.load_products(None)
        else:
            self.pos.load_products(category)