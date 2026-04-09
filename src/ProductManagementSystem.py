import tkinter as tk
from tkinter import ttk
from database_setup import connect_db
from tkinter import messagebox
from Ingredients_Table import IngredientsTableWindow
from Archive import ArchiveFeature

# Main Window
class ProductManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Product Management System")
        self.root.geometry("900x750")

        # Title
        tk.Label(root, text="Product Management System",
                 font=("Arial", 18, "bold")).pack(pady=10)

        # Data Table
        self.tree = ttk.Treeview(root)
        self.tree.pack(fill="both", expand=True)
        
        self.load_products()
        
        self.ingredients_button = tk.Button(
            root,
            text="Manage Ingredients Table",
            width=22,
            command=self.OpenIngredientsTableWindow
        )
        self.ingredients_button.pack(pady=5)
        # Search bar
        self.search_bar = tk.Entry(root, width=24)
        self.search_bar.pack(pady=5)

        # Search button
        self.search_button = tk.Button(root, text="Search Product", width=22,
                                       command=self.search_product)
        self.search_button.pack(pady=5)

        # Refresh button
        self.button = tk.Button(root, text="Refresh Products", width=22,
                                command=self.refresh_products)
        self.button.pack(pady=5)

        # Label
        tk.Label(root, text="Enter Product ID to Delete").pack(pady=5)

        # Frame for entry + button
        delete_frame = tk.Frame(root)
        delete_frame.pack(pady=5)

        # Entry
        self.entry = tk.Entry(delete_frame, width=15)
        self.entry.pack(side=tk.LEFT, padx=5)

        # Delete Button
        self.button_delete = tk.Button(delete_frame, text="Delete", command=self.delete_product)
        self.button_delete.pack(side=tk.LEFT)

        # Add Button
        self.button_add = tk.Button(root, text="Add product", width=22, command=self.OpenAddProductWindow)
        self.button_add.pack(pady=5)

        # Edit Button
        self.button_edit = tk.Button(root, text="Edit Product", width=22, command=self.OpenEditProductWindow)
        self.button_edit.pack(pady=5)

        self.archive_entry = tk.Entry(root, width=30)
        self.archive_entry.pack(pady=20)

        self.archive_button = tk.Button(root, text="Archive Product", width=22, command=self.archive_products)
        self.archive_button.pack(pady=5)

        self.go_to_archive_button = tk.Button(root, text="Go to Archive", width=18, command=self.OpenArchiveFeature)
        self.go_to_archive_button.pack(pady=5)

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
            self.tree.column(col, width=150)

        for row in rows:
            self.tree.insert("", tk.END, values=row)

        conn.close()

    def archive_products(self):
        keyword = self.archive_entry.get()

        if keyword == "":
            messagebox.showwarning("Error", "Please enter a Product ID or Name to archive")
            return

        conn = connect_db()
        cursor = conn.cursor()

        # CHECK IF PRODUCT EXISTS
        cursor.execute("SELECT * FROM products WHERE id=? OR name=?", (keyword, keyword))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", f"Product with ID or Name '{keyword}' not found")
            conn.close()
            return

        # CONFIRM FIRST
        decide = messagebox.askyesno(
            "Confirm Archive",
            f"Are you sure you want to archive product with ID '{keyword}'?"
        )

        if not decide:
            conn.close()
            return

        # ARCHIVE (INSERT INTO ARCHIVE TABLE)
        cursor.execute("""
        INSERT INTO product_archive (name, price, stock)
        SELECT name, price, stock FROM products WHERE id=? OR name=?
        """, (keyword, keyword))

        # DELETE FROM MAIN TABLE
        cursor.execute("DELETE FROM products WHERE id=? OR name=?", (keyword, keyword))

        conn.commit()
        conn.close()

        self.archive_entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Product archived successfully")
        self.refresh_products()

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
            messagebox.showerror("Error", "Please enter a Product ID or Name to delete")
            return

        conn = connect_db()
        cursor = conn.cursor()

        # 🔍 CHECK IF PRODUCT EXISTS
        cursor.execute("""
        SELECT * FROM products
        WHERE id = ? OR name = ?
        """, (keyword, keyword))

        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "Product not found!")
            conn.close()
            return

        # ✅ CONFIRM FIRST
        decide = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{keyword}'?"
        )

        if not decide:
            conn.close()
            return

        # 🗑️ DELETE ONLY AFTER CONFIRMATION
        cursor.execute("""
        DELETE FROM products
        WHERE id = ? OR name = ?
        """, (keyword, keyword))

        conn.commit()
        conn.close()

        self.entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Product deleted successfully")
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

        if product_id == "" or product_name == "" or product_price == "" or product_stock == "":
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
            "INSERT INTO products (id, name, price, stock) VALUES (?, ?, ?, ?)",
            (product_id, product_name, product_price, product_stock)
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
        self.root.geometry("500x400")

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

        self.update_product_button = tk.Button(root, text="Update product", width=18, command=self.update_product)
        self.update_product_button.pack(pady=5)

    def update_product(self):
        product_id = self.update_id.get()
        product_name = self.update_name.get()
        product_price = self.update_price.get()
        product_stock = self.update_stock.get()

        if not product_id:
            messagebox.showerror("Error", "Please enter the Product ID to update")
            return
        
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT name, price, stock FROM products WHERE id=?", (product_id,))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", f"Product with ID {product_id} not found")
            conn.close()
            return
        current_name, current_price, current_stock = result 
        product_name = product_name if product_name.strip() else current_name
        product_price = product_price if product_price.strip() else current_price
        product_stock = product_stock if product_stock.strip() else current_stock

        if product_stock.strip():
            try:
                product_stock = float(product_stock)
            except ValueError:
                messagebox.showerror("Error", "Stock must be a number")
                conn.close()
                return
        else:
            product_stock = current_stock
            
        cursor.execute(
            "UPDATE products SET name=?, price=?, stock=? WHERE id=?",
            (product_name, product_price, product_stock, product_id)
        )

        conn.commit()
        conn.close()

        self.update_id.delete(0, tk.END)
        self.update_name.delete(0, tk.END)
        self.update_price.delete(0, tk.END)
        self.update_stock.delete(0, tk.END)

        messagebox.showinfo("Success", "Product edited successfully")
        self.main_app.refresh_products()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ProductManagementSystem(root)
    root.mainloop()