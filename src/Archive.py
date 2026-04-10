import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox
from database_setup import connect_db

class ArchiveFeature:
    def __init__(self, root):
        self.root = root
        self.root.title("Archive Feature")
        self.root.geometry("1000x600")

        # TITLE
        tk.Label(root, text="Archive Table", font=("Arial", 14, "bold")).pack(pady=10)

        # MAIN FRAME
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True)

        # LEFT FRAME (TABLE)
        left_frame = tk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew")

        # RIGHT FRAME (CONTROLS)
        right_frame = tk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="ns", padx=10)

        # GRID CONFIG
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # =======================
        # TABLE (LEFT)
        # =======================
        self.tree = ttk.Treeview(left_frame)
        self.tree.pack(fill="both", expand=True)

        self.load_products()

        # =======================
        # RIGHT SIDE CONTROLS
        # =======================

        # RELOAD
        tk.Button(right_frame, text="Reload", width=22,
                  command=self.load_products).pack(pady=5)

        # SEARCH
        tk.Label(right_frame, text="Search Product").pack(pady=5)

        self.search_entry = tk.Entry(right_frame, width=25)
        self.search_entry.pack(pady=5)

        tk.Button(right_frame, text="Search", width=22,
                  command=self.search_product).pack(pady=5)

        # UNARCHIVE
        tk.Label(right_frame, text="Unarchive Product").pack(pady=10)

        self.unarchive_entry = tk.Entry(right_frame, width=25)
        self.unarchive_entry.pack(pady=5)

        tk.Button(right_frame, text="Unarchive", width=22,
                  command=self.unarchive_products).pack(pady=5)

        # DELETE
        tk.Label(right_frame, text="Delete Permanently").pack(pady=10)

        self.delete_entry = tk.Entry(right_frame, width=25)
        self.delete_entry.pack(pady=5)

        tk.Button(right_frame, text="Delete", width=22,
                  command=self.delete_product).pack(pady=5)

        # EDIT (still empty function)
        tk.Button(right_frame, text="Edit", width=22).pack(pady=10)

    # =======================
    # FUNCTIONS (UNCHANGED)
    # =======================

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
            self.tree.column(col, width=120)

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

    def delete_product(self):
        keyword = self.delete_entry.get()

        if keyword == "":
            messagebox.showwarning("Warning", "Enter Product ID or Name")
            return
        
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM product_archive WHERE id=? OR name=?", (keyword, keyword))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "Product not found")
            conn.close()
            return
        
        confirm = messagebox.askyesno("Confirm", "Delete permanently?")
        if not confirm:
            conn.close()
            return
        
        cursor.execute("DELETE FROM product_archive WHERE id=? OR name=?", (keyword, keyword))

        conn.commit()
        conn.close()

        self.delete_entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Deleted permanently")
        self.load_products()

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
            messagebox.showerror("Error", "Product not found")
            conn.close()
            return
        
        confirm = messagebox.askyesno("Confirm", "Unarchive this product?")
        if not confirm:
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
        messagebox.showinfo("Success", "Unarchived")
        self.load_products()


# RUN
if __name__ == "__main__":
    root = tk.Tk()
    app = ArchiveFeature(root)
    root.mainloop()