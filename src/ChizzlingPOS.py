import tkinter as tk
from tkinter import messagebox
import sqlite3
from receipt_module import show_receipt_window

# Connect to database
def connect_db():
    return sqlite3.connect("sales_inventory.db")

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

        self.cart = []
        self.total = 0

        self.create_widgets()
        self.load_products()

    def create_widgets(self):
        # Product List
        self.product_listbox = tk.Listbox(self.root, width=40)
        self.product_listbox.grid(row=0, column=0, rowspan=6)

        # Quantity
        tk.Label(self.root, text="Quantity:").grid(row=0, column=1)
        self.qty_entry = tk.Entry(self.root)
        self.qty_entry.grid(row=0, column=2)

        # Buttons
        tk.Button(self.root, text="Add to Cart", command=self.add_to_cart).grid(row=1, column=1, columnspan=2)
        tk.Button(self.root, text="Remove Selected", command=self.remove_item).grid(row=2, column=1, columnspan=2)

        # Cart List
        self.cart_listbox = tk.Listbox(self.root, width=50)
        self.cart_listbox.grid(row=6, column=0, columnspan=3)

        # Total
        self.total_label = tk.Label(self.root, text="Total: 0")
        self.total_label.grid(row=7, column=0)

        # Payment
        tk.Label(self.root, text="Payment:").grid(row=8, column=0)
        self.payment_entry = tk.Entry(self.root)
        self.payment_entry.grid(row=8, column=1)

        tk.Button(self.root, text="Confirm Payment", command=self.confirm_payment).grid(row=9, column=0, columnspan=3)

    def load_products(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price FROM products")
        self.products = cursor.fetchall()
        conn.close()

        for product in self.products:
            self.product_listbox.insert(tk.END, f"{product[1]} - {product[2]}")

    def add_to_cart(self):
        selected = self.product_listbox.curselection()
        if not selected:
            return

        index = selected[0]
        product = self.products[index]

        try:
            qty = int(self.qty_entry.get())
        except:
            messagebox.showerror("Error", "Enter valid quantity")
            return

        subtotal = product[2] * qty
        self.total += subtotal

        self.cart.append((product[0], product[1], qty, subtotal))
        self.cart_listbox.insert(tk.END, f"{product[1]} x{qty} = {subtotal}")

        self.update_total()

    def remove_item(self):
        selected = self.cart_listbox.curselection()
        if not selected:
            return

        index = selected[0]
        item = self.cart[index]

        self.total -= item[3]
        self.cart.pop(index)
        self.cart_listbox.delete(index)

        self.update_total()

    def update_total(self):
        self.total_label.config(text=f"Total: {self.total}")

    def confirm_payment(self):
        try:
            payment = float(self.payment_entry.get())
        except:
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
            cursor.execute("""
                INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal)
                VALUES (?, ?, ?, ?)
            """, (transaction_id, item[0], item[2], item[3]))
            
            cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                           (item[2], item[0]))
        
        cursor.execute("SELECT date FROM transactions WHERE id=?", (transaction_id,))
        date = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()

        show_receipt_window(self.root, transaction_id, date, self.cart, self.total, change)

        messagebox.showinfo("Success", f"Transaction Saved!\nChange: {change}")

        self.cart = []
        self.cart_listbox.delete(0, tk.END)
        self.total = 0
        self.update_total()
        self.payment_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()