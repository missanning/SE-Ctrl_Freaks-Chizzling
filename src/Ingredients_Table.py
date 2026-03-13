import tkinter as tk
from tkinter import ttk
from database_setup import connect_db
from tkinter import messagebox


# Main Window
class IngredientsTableWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Ingredients Table")
        self.root.geometry("900x750")

        # Low stock limit
        self.low_stock_limit = 50

        # Title
        tk.Label(self.root, text="Ingredients Table",
                 font=("Arial", 18, "bold")).pack(pady=10)

        # Data Table
        self.tree = ttk.Treeview(self.root)
        self.tree.pack(fill="both", expand=True)

        self.load_products()

        # Search bar
        self.search_bar2 = tk.Entry(self.root, width=24)
        self.search_bar2.pack(pady=5)

        # Search button
        self.search_button2 = tk.Button(self.root, text="Search Ingredient", width=22,
                                       command=self.search_product)
        self.search_button2.pack(pady=5)

        # Refresh button
        self.button = tk.Button(self.root, text="Refresh Ingredients", width=22,
                                command=self.refresh_products)
        self.button.pack(pady=5)

        # Label
        tk.Label(self.root, text="Enter Ingredient ID to Delete").pack(pady=5)

        # Frame for entry + button
        delete_frame = tk.Frame(self.root)
        delete_frame.pack(pady=5)

        # Entry
        self.entry = tk.Entry(delete_frame, width=15)
        self.entry.pack(side=tk.LEFT, padx=5)

        # Delete Button
        self.button_delete2 = tk.Button(delete_frame, text="Delete", command=self.delete_product)
        self.button_delete2.pack(side=tk.LEFT)

        # Add Button
        self.button_add2 = tk.Button(self.root, text="Add Ingredient", width=22,
                                     command=self.OpenAddProductWindow)
        self.button_add2.pack(pady=5)

        # Edit Button
        self.button_edit2 = tk.Button(self.root, text="Edit Ingredient", width=22,
                                      command=self.OpenEditProductWindow)
        self.button_edit2.pack(pady=5)

    # Load products Ingredients Table
    def load_products(self):
        conn = connect_db()
        cursor = conn.cursor()

        # Display all ingredients
        cursor.execute("SELECT * FROM ingredients")
        rows = cursor.fetchall()

        self.tree.delete(*self.tree.get_children())

        column_names = [desc[0] for desc in cursor.description]

        self.tree["columns"] = column_names
        self.tree["show"] = "headings"

        for col in column_names:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        # Low stock alert system
        low_items = []

        for row in rows:
            stock = row[2]  # stock column

            if stock <= self.low_stock_limit:
                self.tree.insert("", tk.END, values=row, tags=("low",))
                low_items.append(row[1])
            else:
                self.tree.insert("", tk.END, values=row)

        self.tree.tag_configure("low", background="red", foreground="white")

        # Messagebox for low stock alert when opening the inventory management system
        if low_items:
            messagebox.showwarning("Low Stock Alert", f"The following ingredients are low in stock: {', '.join(low_items)}")

        conn.close()

    def refresh_products(self):
        self.load_products()

    def search_product(self):
        keyword = self.search_bar2.get()

        conn = connect_db()
        cursor = conn.cursor()

        # Database query
        cursor.execute("""
        SELECT * FROM ingredients
        WHERE id LIKE ? OR name LIKE ?
        """, ('%' + keyword + '%', '%' + keyword + '%'))

        rows = cursor.fetchall()

        self.tree.delete(*self.tree.get_children())

        for row in rows:
            self.tree.insert("", tk.END, values=row)

        conn.close()

    def delete_product(self):
        product_id = self.entry.get()

        if product_id == "":
            messagebox.showerror("Error", "Please enter an Ingredient ID to delete")
            return

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ingredients WHERE id=?", (product_id,))
        if not cursor.fetchone():
            messagebox.showerror("Error", "Ingredient ID not found")
            conn.close()
            return

        cursor.execute("DELETE FROM ingredients WHERE id=?", (product_id,))
        conn.commit()
        conn.close()

        self.entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Ingredient deleted successfully")
        self.refresh_products()

    def OpenAddProductWindow(self):
        new_window = tk.Toplevel(self.root)
        AddProductWindow2(new_window, self)

    def OpenEditProductWindow(self):
        new_window = tk.Toplevel(self.root)
        EditProductWindow2(new_window, self)


# Add Product Window
class AddProductWindow2:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.root.title("Add Ingredient Window")
        self.root.geometry("500x400")

        # Title
        tk.Label(root, text="Add New Ingredient",
                 font=("Arial", 16, "bold")).pack(pady=10)

        # Name Label and Entry
        tk.Label(root, text="Ingredient Name:").pack(pady=5)
        self.name_entry = tk.Entry(root, width=30)
        self.name_entry.pack(pady=5)

        # Stock Label and Entry
        tk.Label(root, text="Stock:").pack(pady=5)
        self.stock_entry = tk.Entry(root, width=30)
        self.stock_entry.pack(pady=5)

        # Unit Label and Entry
        tk.Label(root, text="Unit:").pack(pady=5)
        self.unit_entry = tk.Entry(root, width=30)
        self.unit_entry.pack(pady=5)

        # Add Button
        tk.Button(root, text="Add Ingredient", command=self.add_product).pack(pady=20)

    def add_product(self):
        name = self.name_entry.get()
        stock = self.stock_entry.get()
        unit = self.unit_entry.get()

        if not name or not stock or not unit:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        try:
            stock = float(stock)
        except ValueError:
            messagebox.showerror("Error", "Stock must be a number")
            return

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO ingredients (name, stock, unit) VALUES (?, ?, ?)",
                       (name, stock, unit))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Ingredient added successfully")
        self.main_app.refresh_products()
        self.root.destroy()


# Edit Product Window
class EditProductWindow2:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.root.title("Edit Ingredient Window")
        self.root.geometry("500x400")

        # Title
        tk.Label(root, text="Edit Ingredient",
                 font=("Arial", 16, "bold")).pack(pady=10)

        # ID Label and Entry
        tk.Label(root, text="Ingredient ID:").pack(pady=5)
        self.id_entry = tk.Entry(root, width=30)
        self.id_entry.pack(pady=5)

        # Name Label and Entry
        tk.Label(root, text="New Name:").pack(pady=5)
        self.name_entry = tk.Entry(root, width=30)
        self.name_entry.pack(pady=5)

        # Stock Label and Entry
        tk.Label(root, text="New Stock:").pack(pady=5)
        self.stock_entry = tk.Entry(root, width=30)
        self.stock_entry.pack(pady=5)

        # Unit Label and Entry
        tk.Label(root, text="New Unit:").pack(pady=5)
        self.unit_entry = tk.Entry(root, width=30)
        self.unit_entry.pack(pady=5)

        # Update Button
        tk.Button(root, text="Update Ingredient", command=self.update_product).pack(pady=20)

    def update_product(self):
        id_val = self.id_entry.get()
        name = self.name_entry.get()
        stock = self.stock_entry.get()
        unit = self.unit_entry.get()

        if not id_val or not name or not stock or not unit:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        try:
            stock = float(stock)
        except ValueError:
            messagebox.showerror("Error", "Stock must be a number")
            return

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ingredients WHERE id=?", (id_val,))
        if not cursor.fetchone():
            messagebox.showerror("Error", "Ingredient ID not found")
            conn.close()
            return

        cursor.execute("UPDATE ingredients SET name=?, stock=?, unit=? WHERE id=?",
                       (name, stock, unit, id_val))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Ingredient updated successfully")
        self.main_app.refresh_products()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = IngredientsTableWindow(root)
    root.mainloop()