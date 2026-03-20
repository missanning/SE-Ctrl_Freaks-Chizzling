import tkinter as tk
from tkinter import messagebox

class CartManager:
    def __init__(self, parent, pos_instance):
        self.parent = parent
        self.pos = pos_instance
        self.cart = []
        self.total = 0
        self.create_cart_frame()
    
    def create_cart_frame(self):
        """Create the checkout/cart frame"""
        self.cart_frame = tk.Frame(self.parent, bg="#FFFFFF", bd=2, relief="raised")
        self.cart_frame.grid(row=1, column=2, rowspan=7, padx=5, pady=10, sticky="ns")
        self.cart_frame.grid_propagate(False)
        self.cart_frame.configure(width=720, height=550)

        # Configure grid
        self.parent.grid_rowconfigure(1, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_columnconfigure(2, weight=0)

        # Title
        tk.Label(self.cart_frame, text="CHECKOUT LIST", font=("Arial", 10, "bold"),
                bg="#FFFFFF").grid(row=0, column=0, columnspan=3, padx=100, pady=5, sticky="ew")

        # Cart items container with scrollbar
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
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
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

        # Configure column weights
        for col, weight in enumerate((4, 1, 1, 1, 2)):
            self.cart_items_frame.grid_columnconfigure(col, weight=weight)

        # Cart frame grid configuration
        self.cart_frame.grid_rowconfigure(1, weight=1)
        self.cart_frame.grid_columnconfigure(0, weight=1)

        # Total label
        self.total_label = tk.Label(self.cart_frame, text="Total: 0", bg="#FFFFFF", font=("Arial", 10, "bold"))
        self.total_label.grid(row=2, column=0, columnspan=3, pady=(10, 5), sticky="w", padx=10)

        # Payment section
        tk.Label(self.cart_frame, text="Payment:", bg="#FFFFFF").grid(row=4, column=0, sticky="w", padx=10)
        self.payment_entry = tk.Entry(self.cart_frame)
        self.payment_entry.grid(row=4, column=1, columnspan=2, pady=5, sticky="ew", padx=10)

        # Confirm payment button
        tk.Button(self.cart_frame, text="Confirm Payment", command=self.pos.confirm_payment,
                  bg="#28A745", fg="white", activebackground="#3DC06B", activeforeground="white",
                  relief="raised").grid(row=5, column=0, columnspan=3, pady=10, padx=10, sticky="ew")
        
        # Initialize with header only
        self.update_cart()
    
    def add_item(self, product_id, name, price, qty):
        """Add item to cart or update quantity if exists"""
        # Check if product already in cart
        for item in self.cart:
            if item['id'] == product_id:
                item['qty'] += qty
                self.update_cart()
                return
        
        # Add new product to cart
        self.cart.append({'id': product_id, 'name': name, 'price': price, 'qty': qty})
        self.update_cart()
        self.update_total()
    
    def update_cart(self):
        """Update the cart display"""
        # Clear current items
        for widget in self.cart_items_frame.winfo_children():
            widget.destroy()

        # Header row
        header_bg = "#FFFFFF"
        tk.Label(self.cart_items_frame, text="Name", bg=header_bg, width=18).grid(row=0, column=0, sticky="w", padx=10)
        tk.Label(self.cart_items_frame, text="", bg=header_bg, width=2).grid(row=0, column=1)
        tk.Label(self.cart_items_frame, text="QTY", bg=header_bg, width=6).grid(row=0, column=2)
        tk.Label(self.cart_items_frame, text="", bg=header_bg, width=2).grid(row=0, column=3)
        tk.Label(self.cart_items_frame, text="PRICE", bg=header_bg, width=8).grid(row=0, column=4, sticky="e", padx=10)

        # Cart items
        for i, item in enumerate(self.cart):
            row = i + 1
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
        
        self.update_total()
    
    def change_qty(self, index, delta):
        """Change quantity of item in cart"""
        self.cart[index]['qty'] += delta

        if self.cart[index]['qty'] <= 0:
            self.cart.pop(index)

        self.update_cart()
    
    def update_total(self):
        """Update the total price display"""
        self.total = sum(item['price'] * item['qty'] for item in self.cart)
        self.total_label.config(text=f"Total: {self.total:.2f}")
    
    def clear_cart(self):
        """Clear all items from cart"""
        self.cart = []
        self.update_cart()
        if hasattr(self, 'payment_entry'):
            self.payment_entry.delete(0, tk.END)
    
    def cancel_order(self):
        """Cancel the current order"""
        if not self.cart:
            messagebox.showinfo("Info", "Cart is already empty")
            return
        
        response = messagebox.askyesno("Cancel Order", "Are you sure you want to cancel all items in the cart?")
        if response:
            self.clear_cart()
            messagebox.showinfo("Success", "All items have been removed from cart")