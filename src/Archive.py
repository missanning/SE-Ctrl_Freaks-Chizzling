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

        self.search_entry = tk.Entry(root, width=30)
        self.search_entry.pack(pady=20)

        self.search_button = tk.Button(root, text="Search", width=27)
        self.search_button.pack(pady=10)

        self.unarchive_entry = tk.Entry(root, width=30)
        self.unarchive_entry.pack(pady=20)

        self.unarchive_button = tk.Button(root, text="Unarchive", width=27)
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
if __name__ == "__main__":
    root = tk.Tk()
    app = ArchiveFeature(root)
    root.mainloop()