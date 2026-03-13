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
        self.search_button2 = tk.Button(self.root, text="Search Product", width=22,
                                        command=self.search_product)
        self.search_button2.pack(pady=5)

        # Refresh button
        self.button = tk.Button(self.root, text="Refresh Products", width=22,
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

        # Display all ingreidients
        cursor.execute("SELECT * FROM ingredients") # Change to ingredients table
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

        self.tree.tag_configure("low", background="red", foreground="white") # Color for low stock items

        # Messagebox for low stock alert when opening the inventory management system
        if low_items:
            messagebox.showwarning(
                "Low Stock Alert",
                "Low stock detected for:\n" + "\n".join(low_items)
            )

        conn.close()

    # Refresh products
    def refresh_products(self):
        self.load_products()

    # Search Products
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

    # Delete ingredients
    def delete_product(self):
        ingredient_id = self.entry.get()

        if ingredient_id == "":
            return

        conn = connect_db()
        cursor = conn.cursor()

        # Database query
        cursor.execute("DELETE FROM ingredients WHERE id=?", (ingredient_id,))
        conn.commit()
        conn.close()

        # Messagebox for successful deletion
        self.entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Ingredient deleted successfully")
        self.refresh_products()

    # Open Add items Window
    def OpenAddProductWindow(self):
        new_window = tk.Toplevel(self.root)
        AddProductWindow2(new_window, self)

    # Open Edit items Window
    def OpenEditProductWindow(self):
        new_window = tk.Toplevel(self.root)
        EditProductWindow2(new_window, self)


# Add Ingredient Window
class AddProductWindow2:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.root.title("Add Ingredient Window")
        self.root.geometry("500x400")

        # Label and Entry widgets

        # Main title text
        tk.Label(self.root, text="Add New Ingredient", font=("Arial", 16, "bold")).pack(pady=10)

        # Ingredient ID label and Entry
        tk.Label(self.root, text="Ingredient ID:").pack(pady=5)
        self.ingredient_id = tk.Entry(self.root, width=20)
        self.ingredient_id.pack(pady=5)

        # Ingredient Name label and Entry
        tk.Label(self.root, text="Ingredient Name:").pack(pady=5)
        self.ingredient_name = tk.Entry(self.root, width=20)
        self.ingredient_name.pack(pady=5)

        # Ingredient Unit label and entry
        tk.Label(self.root, text="Ingredient Unit:").pack(pady=5)
        self.ingredient_unit = tk.Entry(self.root, width=20)
        self.ingredient_unit.pack(pady=5)

        # Ingredient Stock label and entry
        tk.Label(self.root, text="Ingredient Stock:").pack(pady=5)
        self.ingredient_stock = tk.Entry(self.root, width=20)
        self.ingredient_stock.pack(pady=5)

        # Submit Button
        tk.Button(self.root, text="Add Ingredient", width=18,
                  command=self.add_product).pack(pady=5)

    def add_product(self):
        ingredient_id = self.ingredient_id.get()
        ingredient_name = self.ingredient_name.get()
        ingredient_unit = self.ingredient_unit.get()
        ingredient_stock = self.ingredient_stock.get()

        if ingredient_id == "" or ingredient_name == "" or ingredient_unit == "" or ingredient_stock == "":
            return

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO ingredients (id, name, stock, unit) VALUES (?, ?, ?, ?)",
            (ingredient_id, ingredient_name, ingredient_stock, ingredient_unit)
        )

        conn.commit()
        conn.close()

        self.ingredient_id.delete(0, tk.END)
        self.ingredient_name.delete(0, tk.END)
        self.ingredient_unit.delete(0, tk.END)
        self.ingredient_stock.delete(0, tk.END)

        messagebox.showinfo("Success", "Ingredient added successfully")
        self.main_app.refresh_products()


# Edit Ingredient Window
class EditProductWindow2:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.root.title("Edit Ingredient Window")
        self.root.geometry("500x400")

         # Label and Entry widgets

        # Main title text
        tk.Label(self.root, text="Update Existing Ingredient", font=("Arial", 16, "bold")).pack(pady=10)

        # Ingredient ID label and Entry
        tk.Label(self.root, text="Ingredient ID:").pack(pady=5)
        self.ingredient_id = tk.Entry(self.root, width=20)
        self.ingredient_id.pack(pady=5)

        # Ingredient Name label and Entry
        tk.Label(self.root, text="Update Ingredient Name:").pack(pady=5)
        self.ingredient_name = tk.Entry(self.root, width=20)
        self.ingredient_name.pack(pady=5)

        # Ingredient Unit label and Entry
        tk.Label(self.root, text="Update Ingredient Unit:").pack(pady=5)
        self.ingredient_unit = tk.Entry(self.root, width=20)
        self.ingredient_unit.pack(pady=5)

        # Ingredient Stock label and Entry
        tk.Label(self.root, text="Update Ingredient Stock:").pack(pady=5)
        self.ingredient_stock = tk.Entry(self.root, width=20)
        self.ingredient_stock.pack(pady=5)

        tk.Button(self.root, text="Update Ingredient", width=18,
                  command=self.update_product).pack(pady=5)

    def update_product(self):
        ingredient_id = self.ingredient_id.get()
        ingredient_name = self.ingredient_name.get()
        ingredient_unit = self.ingredient_unit.get()
        ingredient_stock = self.ingredient_stock.get()

        if ingredient_id == "" or ingredient_name == "" or ingredient_unit == "" or ingredient_stock == "":
            return

        try:
                conn = connect_db()
                cursor = conn.cursor()

                cursor.execute(
                    "UPDATE ingredients SET name=?, stock=?, unit=? WHERE id=?",
                    (ingredient_name, ingredient_stock, ingredient_unit, ingredient_id)
                )

                conn.commit()

        except Exception as e:
                messagebox.showerror("Error", str(e))

        finally:
                conn.close()

        self.ingredient_id.delete(0, tk.END)
        self.ingredient_name.delete(0, tk.END)
        self.ingredient_unit.delete(0, tk.END)
        self.ingredient_stock.delete(0, tk.END)

        messagebox.showinfo("Success", "Ingredient updated successfully")
        self.main_app.refresh_products()


if __name__ == "__main__":
    root = tk.Tk()
    app = IngredientsTableWindow(root)
    root.mainloop()