import tkinter as tk
from tkinter import ttk
from database_setup import connect_db
from tkinter import messagebox
from Ingredients_Table import IngredientsTableWindow
from Archive import ArchiveFeature
from LoginPage import MainApp
"""
Product Management System, Ingredients table, archive fixed GUI and added features:
- Added category field to products
- Fixed add and update bugs
- Updated GUI for better user experience"""
class ProductManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Product Management System")
        self.root.geometry("1200x600")

        # TITLE
        tk.Label(root, text="Product Management System",
                 font=("Arial", 18, "bold")).pack(pady=10)

        # MAIN FRAME
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True)

        # LEFT (TABLE)
        left_frame = tk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew")

        # RIGHT (BUTTONS)
        right_frame = tk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="ns", padx=10)

        # GRID CONFIG
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(left_frame)
        self.tree.pack(fill="both", expand=True)

        self.load_products()

        # INGREDIENTS
        tk.Button(right_frame, text="Manage Ingredients Table", width=22,
                  command=self.OpenIngredientsTableWindow).pack(pady=5)

        # SEARCH
        self.search_bar = tk.Entry(right_frame, width=24)
        self.search_bar.pack(pady=5)

        tk.Button(right_frame, text="Search Product", width=22,
                  command=self.search_product).pack(pady=5)

        # REFRESH
        tk.Button(right_frame, text="Refresh Products", width=22,
                  command=self.refresh_products).pack(pady=5)

        # DELETE SECTION
        tk.Label(right_frame, text="Enter Product ID to Delete").pack(pady=5)

        delete_frame = tk.Frame(right_frame)
        delete_frame.pack(pady=5)

        self.entry = tk.Entry(delete_frame, width=15)
        self.entry.pack(side=tk.LEFT, padx=5)

        tk.Button(delete_frame, text="Delete",
                  command=self.delete_product).pack(side=tk.LEFT)

        # ADD / EDIT
        tk.Button(right_frame, text="Add Product", width=22,
                  command=self.OpenAddProductWindow).pack(pady=5)

        tk.Button(right_frame, text="Edit Product", width=22,
                  command=self.OpenEditProductWindow).pack(pady=5)

        # ARCHIVE
        self.archive_entry = tk.Entry(right_frame, width=24)
        self.archive_entry.pack(pady=10)

        tk.Button(right_frame, text="Archive Product", width=22,
                  command=self.archive_products).pack(pady=5)

        tk.Button(right_frame, text="Go to Archive", width=22,
                  command=self.OpenArchiveFeature).pack(pady=5)

        # LOGOUT
        tk.Button(right_frame, text="Logout", width=22,
                  command=self.OpenLoginPage).pack(pady=20)

    def load_products(self):
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()

        self.tree.delete(*self.tree.get_children())

        column_names = [desc[0] for desc in cursor.description]

        self.tree["columns"] = column_names
        self.tree["show"] = "headings"

        for col in column_names:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        for row in rows:
            self.tree.insert("", tk.END, values=row)

        conn.close()

    def refresh_products(self):
        self.load_products()

    def search_product(self):
        keyword = self.search_bar.get()

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM products
        WHERE id LIKE ? OR name LIKE ?
        """, ('%' + keyword + '%', '%' + keyword + '%'))

        rows = cursor.fetchall()

        self.tree.delete(*self.tree.get_children())

        for row in rows:
            self.tree.insert("", tk.END, values=row)

        conn.close()

    def delete_product(self):
        keyword = self.entry.get()

        if keyword == "":
            messagebox.showerror("Error", "Enter ID or Name")
            return

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products WHERE id=? OR name=?", (keyword, keyword))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "Product not found!")
            conn.close()
            return

        confirm = messagebox.askyesno("Confirm", "Delete this product?")
        if not confirm:
            conn.close()
            return

        cursor.execute("DELETE FROM products WHERE id=? OR name=?", (keyword, keyword))

        conn.commit()
        conn.close()

        self.entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Deleted")
        self.refresh_products()

    def archive_products(self):
        keyword = self.archive_entry.get()

        if keyword == "":
            messagebox.showwarning("Error", "Enter ID or Name")
            return

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products WHERE id=? OR name=?", (keyword, keyword))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "Not found")
            conn.close()
            return

        confirm = messagebox.askyesno("Confirm", "Archive this product?")
        if not confirm:
            conn.close()
            return

        cursor.execute("""
        INSERT INTO product_archive (name, price, stock)
        SELECT name, price, stock FROM products WHERE id=? OR name=?
        """, (keyword, keyword))

        cursor.execute("DELETE FROM products WHERE id=? OR name=?", (keyword, keyword))

        conn.commit()
        conn.close()

        self.archive_entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Archived")
        self.refresh_products()

    def OpenAddProductWindow(self):
        new_window = tk.Toplevel(self.root)
        AddProductWindow(new_window, self)

    def OpenEditProductWindow(self):
        new_window = tk.Toplevel(self.root)
        EditProductWindow(new_window, self)

    def OpenIngredientsTableWindow(self):
        new_window = tk.Toplevel(self.root)
        IngredientsTableWindow(new_window)

    def OpenArchiveFeature(self):
        new_window = tk.Toplevel(self.root)
        ArchiveFeature(new_window)

    def OpenLoginPage(self):
        self.root.destroy()
        new_window = tk.Tk()
        MainApp(new_window)


# Add Product Window
class AddProductWindow:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.root.title("Add Product Window")
        self.root.geometry("500x400")

        tk.Label(root, text="Add New Product", font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(root, text="Product Name:").pack(pady=5)
        self.entry_name = tk.Entry(root, width=20)
        self.entry_name.pack(pady=5)

        tk.Label(root, text="Product Price:").pack(pady=5)
        self.entry_price = tk.Entry(root, width=20)
        self.entry_price.pack(pady=5)

        tk.Label(root, text="Product stock:").pack(pady=5)
        self.entry_stock = tk.Entry(root, width=20)
        self.entry_stock.pack(pady=5)

        tk.Label(root, text="Product Category:").pack(pady=5)
        self.entry_category = tk.Entry(root, width=20)
        self.entry_category.pack(pady=5)

        self.add_product_button = tk.Button(root, text="Add product", width=18, command=self.add_product)
        self.add_product_button.pack(pady=5)

    def get_next_id(self):
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM products ORDER BY id ASC")
        ids = cursor.fetchall()

        conn.close()

        expected_id = 1

        for row in ids:
            current_id = int(row[0])
            if current_id != expected_id:
                return expected_id
            expected_id += 1

        return expected_id


    def add_product(self):
        product_id = self.get_next_id()
        product_name = self.entry_name.get()
        product_price = self.entry_price.get()
        product_stock = self.entry_stock.get()
        product_category = self.entry_category.get()

        if product_id == "" or product_name == "" or product_price == "" or product_stock == "" or product_category == "":
            messagebox.showerror("Error", "Please fill in all fields")
            return

        conn = connect_db()
        cursor = conn.cursor()

        # ✅ CHECK BY NAME (NOT ID)
        cursor.execute("SELECT * FROM products WHERE name=?", (product_name,))
        existing = cursor.fetchone()

        if existing:
            messagebox.showerror("Error", f"Product '{product_name}' already exists!")
            conn.close()
            return

        # INSERT
        cursor.execute(
            "INSERT INTO products (id, name, price, stock, category) VALUES (?, ?, ?, ?, ?)",
            (product_id, product_name, product_price, product_stock, product_category)
        )

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Product added successfully")
        self.main_app.refresh_products()


# Edit Product Window
class EditProductWindow:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.root.title("Edit Product Window")
        self.root.geometry("500x500")

        tk.Label(root, text="Update Existing Product", font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(root, text="Product ID:").pack(pady=5)
        self.update_id = tk.Entry(root, width=20)
        self.update_id.pack(pady=5)

        tk.Label(root, text="Update Product Name:").pack(pady=5)
        self.update_name = tk.Entry(root, width=20)
        self.update_name.pack(pady=5)

        tk.Label(root, text="Update Product Price:").pack(pady=5)
        self.update_price = tk.Entry(root, width=20)
        self.update_price.pack(pady=5)

        tk.Label(root, text="Update Product stock:").pack(pady=5)
        self.update_stock = tk.Entry(root, width=20)
        self.update_stock.pack(pady=5)

        tk.Label(root, text="Update Product Category:").pack(pady=5)
        self.update_category = tk.Entry(root, width=20)
        self.update_category.pack(pady=5)

        self.update_product_button = tk.Button(root, text="Update product", width=18, command=self.update_product)
        self.update_product_button.pack(pady=5)

    def update_product(self):
        product_id = self.update_id.get()
        product_name = self.update_name.get()
        product_price = self.update_price.get()
        product_stock = self.update_stock.get()
        product_category = self.update_category.get()

        if not product_id:
            messagebox.showerror("Error", "Please enter the Product ID to update")
            return
        
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT name, price, stock, category FROM products WHERE id=?", (product_id,))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", f"Product with ID {product_id} not found")
            conn.close()
            return
        current_name, current_price, current_stock, current_category = result
        product_name = product_name if product_name.strip() else current_name
        product_price = product_price if product_price.strip() else current_price
        product_stock = product_stock if product_stock.strip() else current_stock
        product_category = product_category if product_category.strip() else current_category

        if product_stock.strip():
            try:
                product_stock = float(product_stock)
            except ValueError:
                messagebox.showerror("Error", "Stock must be a number")
                conn.close()
                return
        else:
            product_stock = current_stock

        if product_category.strip():
            product_category = product_category
        else:
            product_category = current_category

        cursor.execute(
            "UPDATE products SET name=?, price=?, stock=?, category=? WHERE id=?",
            (product_name, product_price, product_stock, product_category, product_id)
        )

        conn.commit()
        conn.close()

        self.update_id.delete(0, tk.END)
        self.update_name.delete(0, tk.END)
        self.update_price.delete(0, tk.END)
        self.update_stock.delete(0, tk.END)
        self.update_category.delete(0, tk.END)

        messagebox.showinfo("Success", "Product edited successfully")
        self.main_app.refresh_products()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ProductManagementSystem(root)
    root.mainloop()