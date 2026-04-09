import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox
from database_setup import connect_db

class ArchiveFeature:
    def __init__(self, root):
        self.root = root
        self.root.title("Archive Feature")
        self.root.geometry("900x750")

        tk.Label(root, text="Archive Table", font=("Arial", 12, "bold")).pack(pady=10)

        self.tree = ttk.Treeview(root)
        self.tree.pack(fill="both", expand=True)
        
        self.load_products()

        self.reload_button = tk.Button(root, text="Reload", width=27, command=self.load_products)
        self.reload_button.pack(pady=10)
        
        self.search_entry = tk.Entry(root, width=30)
        self.search_entry.pack(pady=20)

        self.search_button = tk.Button(root, text="Search", width=27, command=self.search_product)
        self.search_button.pack(pady=10)

        self.unarchive_entry = tk.Entry(root, width=30)
        self.unarchive_entry.pack(pady=20)

        self.unarchive_button = tk.Button(root, text="Unarchive", width=27, command=self.unarchive_products)
        self.unarchive_button.pack(pady=10)

        self.delete_entry = tk.Entry(root, width=30)
        self.delete_entry.pack(pady=20)

        self.delete_button = tk.Button(root, text="Delete", width=27)
        self.delete_button.pack(pady=10)

        self.edit_button = tk.Button(root, text="Edit", width=27)
        self.edit_button.pack(pady=10)

    def load_products(self):
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM product_archive")
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

    def search_product(self):
        keyword = self.search_entry.get()

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM product_archive
        WHERE id LIKE ? OR name LIKE ?
        """, ('%' + keyword + '%', '%' + keyword + '%'))

        rows = cursor.fetchall()

        self.tree.delete(*self.tree.get_children())

        for row in rows:
            self.tree.insert("", tk.END, values=row)

        conn.close()

    def unarchive_products(self):
        keyword = self.unarchive_entry.get()

        if keyword == "":
            messagebox.showwarning("Warning", "Enter Product ID or Name")
            return
        
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM product_archive WHERE id=? OR name=?", (keyword, keyword))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", f"Product with ID or Name '{keyword}' not found in archive")
            conn.close()
            return
        
        decide = messagebox.askyesno(
            "Confirm Unarchive",
            f"Are you sure you want to unarchive product with ID or Name '{keyword}'?"
        )

        
        if not decide:
            conn.close()
            return
        
        cursor.execute("""
        INSERT INTO products (name, price, stock)
        SELECT name, price, stock FROM product_archive WHERE id=? OR name=?
        """, (keyword, keyword))

        cursor.execute("DELETE FROM product_archive WHERE id=? OR name=?", (keyword, keyword))

        conn.commit()
        conn.close()

        self.unarchive_entry.delete(0, tk.END)
        messagebox.showinfo("Success", f"Product with ID or Name '{keyword}' has been unarchived")
        self.load_products()

if __name__ == "__main__":
    root = tk.Tk()
    app = ArchiveFeature(root)
    root.mainloop()