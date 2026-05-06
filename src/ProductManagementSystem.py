import tkinter as tk
from tkinter import ttk, messagebox
import os
from database_setup import connect_db
from Ingredients_Table import IngredientsTableWindow
from Archive import ArchiveFeature

# ── Color palette (matches LoginPage) ──────────────────────────
BG         = "#ffffff"
ACCENT     = "#f5a623"
YELLOW     = "#ffd966"
BROWN      = "#7a3b10"
FG         = "#3b1f0a"
SUBTLE     = "#7a3b10"
ENTRY_BG   = "#fff8ee"
ENTRY_BORDER = "#f5a623"

FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_LABEL  = ("Segoe UI", 10, "bold")
FONT_ENTRY  = ("Segoe UI", 10)
FONT_BTN    = ("Segoe UI", 10, "bold")
FONT_SMALL  = ("Segoe UI", 9)

CATEGORIES = ["meals", "snacks", "drinks", "alcohol"]


def styled_button(parent, text, command, bg=BROWN, fg=YELLOW, width=20):
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=ACCENT, activeforeground=BROWN,
        font=FONT_BTN, relief="flat", bd=0, padx=10, pady=6,
        cursor="hand2", width=width
    )


def entry_field(parent, label_text, var=None):
    """Returns a labeled entry with LoginPage styling."""
    tk.Label(parent, text=label_text, font=FONT_LABEL,
             bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))
    border = tk.Frame(parent, bg=ENTRY_BORDER, padx=1, pady=1)
    border.pack(fill="x", pady=(2, 0))
    e = tk.Entry(border, font=FONT_ENTRY, bg=ENTRY_BG, fg=FG,
                 relief="flat", bd=0, textvariable=var)
    e.pack(fill="x", ipady=6, padx=4)
    e.bind("<FocusIn>",  lambda ev: border.config(bg=ACCENT))
    e.bind("<FocusOut>", lambda ev: border.config(bg=ENTRY_BORDER))
    return e


def _apply_combo_style():
    """Apply cream background style to Combobox matching other entry fields."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Cream.TCombobox",
                    fieldbackground=ENTRY_BG,
                    background=ENTRY_BG,
                    foreground=FG,
                    selectbackground=ENTRY_BG,
                    selectforeground=FG,
                    arrowcolor=BROWN)
    style.map("Cream.TCombobox",
              fieldbackground=[("readonly", ENTRY_BG)],
              background=[("readonly", ENTRY_BG)])


class ProductManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Chizzling — Product Management")
        self.root.state("zoomed")
        self.root.configure(bg=BG)
        self.stocks = 30

        self._build_ui()
        self.load_products()
        self.root.after(100, self.root.focus_force)
        self.root.bind_all("<Button-1>", self._fix_focus, add="+")

    def _fix_focus(self, event):
        if isinstance(event.widget, tk.Entry):
            event.widget.focus_set()

    # ── UI Layout ───────────────────────────────────────────────

    def _build_ui(self):
        # Top banner
        banner = tk.Frame(self.root, bg=BROWN, height=42)
        banner.pack(fill="x", side="top")
        banner.pack_propagate(False)

        tk.Label(banner, text="Chizzling POS  ·  Product Management",
                 font=FONT_TITLE, bg=BROWN, fg=YELLOW).pack(side="left", padx=16, pady=8)

        styled_button(banner, "⎋  Logout", self._logout,
                      bg=BROWN, fg=YELLOW, width=12).pack(side="right", padx=12, pady=6)

        tk.Frame(self.root, bg=ACCENT, height=4).pack(fill="x")
        tk.Frame(self.root, bg=YELLOW, height=4).pack(fill="x")

        # Body
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        # Left — table
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        self._build_table(left)

        # Right — controls
        right = tk.Frame(body, bg=BG, width=220)
        right.pack(side="right", fill="y", padx=(16, 0))
        right.pack_propagate(False)

        self._build_controls(right)

        # Bottom strip
        tk.Frame(self.root, bg=YELLOW, height=4).pack(fill="x", side="bottom")
        tk.Frame(self.root, bg=ACCENT, height=4).pack(fill="x", side="bottom")
        tk.Frame(self.root, bg=BROWN, height=8).pack(fill="x", side="bottom")

    def _build_table(self, parent):
        # Search bar row
        search_row = tk.Frame(parent, bg=BG)
        search_row.pack(fill="x", pady=(0, 10))

        tk.Label(search_row, text="Search:", font=FONT_LABEL,
                 bg=BG, fg=BROWN).pack(side="left", padx=(0, 6))

        search_border = tk.Frame(search_row, bg=ENTRY_BORDER, padx=1, pady=1)
        search_border.pack(side="left", fill="x", expand=True)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self.search_product())
        search_entry = tk.Entry(search_border, textvariable=self.search_var,
                                font=FONT_ENTRY, bg=ENTRY_BG, fg=FG,
                                relief="flat", bd=0)
        search_entry.pack(fill="x", ipady=6, padx=4)
        search_entry.bind("<FocusIn>",  lambda e: search_border.config(bg=ACCENT))
        search_entry.bind("<FocusOut>", lambda e: search_border.config(bg=ENTRY_BORDER))

        styled_button(search_row, "↺  Refresh", self.load_products,
                      width=12).pack(side="right", padx=(8, 0))

        # Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Chizzling.Treeview",
                        background=ENTRY_BG, fieldbackground=ENTRY_BG,
                        foreground=FG, font=FONT_ENTRY, rowheight=28)
        style.configure("Chizzling.Treeview.Heading",
                        background=BROWN, foreground=YELLOW,
                        font=FONT_LABEL, relief="flat")
        style.map("Chizzling.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", BROWN)])

        tree_frame = tk.Frame(parent, bg=BROWN, padx=1, pady=1)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, style="Chizzling.Treeview",
                                 selectmode="browse")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _build_controls(self, parent):
        tk.Label(parent, text="Actions", font=FONT_TITLE,
                 bg=BG, fg=BROWN).pack(anchor="w", pady=(0, 4))
        tk.Frame(parent, bg=YELLOW, height=3).pack(fill="x", pady=(0, 12))

        styled_button(parent, "＋  Add Product",
                      self.OpenAddProductWindow).pack(fill="x", pady=4)
        styled_button(parent, "✎  Edit Product",
                      self.OpenEditProductWindow).pack(fill="x", pady=4)

        tk.Frame(parent, bg=YELLOW, height=2).pack(fill="x", pady=10)

        tk.Label(parent, text="Archive by ID or Name",
                 font=FONT_SMALL, bg=BG, fg=SUBTLE).pack(anchor="w")

        arc_border = tk.Frame(parent, bg=ENTRY_BORDER, padx=1, pady=1)
        arc_border.pack(fill="x", pady=(2, 6))
        self.archive_entry = tk.Entry(arc_border, font=FONT_ENTRY,
                                      bg=ENTRY_BG, fg=FG, relief="flat", bd=0)
        self.archive_entry.pack(fill="x", ipady=6, padx=4)
        self.archive_entry.bind("<FocusIn>",  lambda e: arc_border.config(bg=ACCENT))
        self.archive_entry.bind("<FocusOut>", lambda e: arc_border.config(bg=ENTRY_BORDER))

        styled_button(parent, "📦  Archive Product",
                      self.archive_products,
                      bg="#a0522d", fg=YELLOW).pack(fill="x", pady=4)

        styled_button(parent, "🗂  View Archive",
                      self.OpenArchiveFeature,
                      bg=SUBTLE, fg=YELLOW).pack(fill="x", pady=4)

        tk.Frame(parent, bg=YELLOW, height=2).pack(fill="x", pady=10)

        styled_button(parent, "🧪  Manage Ingredients",
                      self.OpenIngredientsTableWindow,
                      bg=ACCENT, fg=BROWN).pack(fill="x", pady=4)

    # ── Data ────────────────────────────────────────────────────

    def load_products(self, *_):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        conn.close()

        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = col_names
        self.tree["show"] = "headings"

        for col in col_names:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=120, anchor="center")

        low_items = []
        for row in rows:
            stock = row[3]
            if stock <= self.stocks:
                self.tree.insert("", tk.END, values=row, tags=("low",))
                low_items.append(row[1])
            else:
                self.tree.insert("", tk.END, values=row)

        self.tree.tag_configure("low", background="#ffe0e0", foreground="#c0392b")

        if low_items:
            messagebox.showwarning("Low Stock Alert",
                                   f"Low stock items:\n• " + "\n• ".join(low_items))

    def search_product(self):
        keyword = self.search_var.get()
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE id LIKE ? OR name LIKE ?",
            (f"%{keyword}%", f"%{keyword}%")
        )
        rows = cursor.fetchall()
        conn.close()

        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def archive_products(self):
        keyword = self.archive_entry.get().strip()
        if not keyword:
            messagebox.showwarning("Archive", "Enter a product ID or name.")
            return

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id=? OR name=?", (keyword, keyword))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Not Found", "Product not found.")
            conn.close()
            return

        if not messagebox.askyesno("Confirm Archive", f"Archive '{result[1]}'?"):
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
        messagebox.showinfo("Archived", "Product archived successfully.")
        self.load_products()

    # ── Navigation ──────────────────────────────────────────────

    def OpenAddProductWindow(self):
        AddProductWindow(tk.Toplevel(self.root), self)

    def OpenEditProductWindow(self):
        EditProductWindow(tk.Toplevel(self.root), self)

    def OpenIngredientsTableWindow(self):
        IngredientsTableWindow(tk.Toplevel(self.root))

    def OpenArchiveFeature(self):
        ArchiveFeature(tk.Toplevel(self.root))

    def _logout(self):
        from LoginPage import MainApp
        self.root.destroy()
        new_root = tk.Tk()
        MainApp(new_root)
        new_root.mainloop()


# ── Add Product Window ──────────────────────────────────────────

class AddProductWindow:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.root.title("Add Product")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.grab_set()
        self.root.after(100, self.root.focus_force)
        self._image_path = None  # selected source image path
        self._preview_img = None

        w, h = 420, 580
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Banner
        banner = tk.Frame(root, bg=BROWN, height=38)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        tk.Label(banner, text="Add New Product", font=FONT_TITLE,
                 bg=BROWN, fg=YELLOW).pack(side="left", padx=14, pady=6)

        tk.Frame(root, bg=ACCENT, height=3).pack(fill="x")
        tk.Frame(root, bg=YELLOW, height=3).pack(fill="x")

        form = tk.Frame(root, bg=BG, padx=30, pady=16)
        form.pack(fill="both", expand=True)

        self.e_name     = entry_field(form, "Product Name")
        self.e_price    = entry_field(form, "Price (₱)")
        self.e_stock    = entry_field(form, "Stock")

        # Category dropdown
        tk.Label(form, text="Category", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))
        cat_border = tk.Frame(form, bg=ENTRY_BORDER, padx=1, pady=1)
        cat_border.pack(fill="x", pady=(2, 0))
        self.cat_var = tk.StringVar(value=CATEGORIES[0])
        cat_menu = tk.OptionMenu(cat_border, self.cat_var, *CATEGORIES)
        cat_menu.config(bg=ENTRY_BG, fg=FG, activebackground=ACCENT,
                        activeforeground=FG, font=FONT_ENTRY,
                        relief="flat", bd=0, highlightthickness=0,
                        anchor="w", width=30)
        cat_menu["menu"].config(bg=ENTRY_BG, fg=FG, activebackground=ACCENT,
                                activeforeground=FG, font=FONT_ENTRY)
        cat_menu.pack(fill="x", padx=2, pady=2)

        # Image upload
        tk.Label(form, text="Product Image  (required)", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))

        img_row = tk.Frame(form, bg=BG)
        img_row.pack(fill="x", pady=(4, 0))

        # Preview box
        self.preview_lbl = tk.Label(img_row, bg=ENTRY_BG, width=10, height=5,
                                    text="No image", font=FONT_SMALL, fg=SUBTLE,
                                    relief="flat",
                                    highlightbackground=ENTRY_BORDER, highlightthickness=1)
        self.preview_lbl.pack(side="left", padx=(0, 10))

        btn_col = tk.Frame(img_row, bg=BG)
        btn_col.pack(side="left", fill="y")
        styled_button(btn_col, "📁  Browse Image", self._browse_image,
                      bg=ACCENT, fg=BROWN, width=16).pack(pady=(0, 4))
        self.img_name_lbl = tk.Label(btn_col, text="", font=FONT_SMALL,
                                     bg=BG, fg=SUBTLE, wraplength=160, justify="left")
        self.img_name_lbl.pack(anchor="w")

        styled_button(form, "＋  Add Product", self._add, width=22).pack(pady=(16, 0), fill="x")

    def _browse_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select Product Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )
        if not path:
            return
        self._image_path = path
        self.img_name_lbl.config(text=os.path.basename(path))
        # Show preview
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).resize((80, 60), Image.LANCZOS)
            self._preview_img = ImageTk.PhotoImage(img)
            self.preview_lbl.config(image=self._preview_img, text="")
        except Exception:
            self.preview_lbl.config(text="Preview\nunavailable")

    def _get_next_id(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products ORDER BY id ASC")
        ids = [r[0] for r in cursor.fetchall()]
        conn.close()
        expected = 1
        for i in ids:
            if int(i) != expected:
                return expected
            expected += 1
        return expected

    def _add(self):
        import shutil
        name     = self.e_name.get().strip()
        price    = self.e_price.get().strip()
        stock    = self.e_stock.get().strip()
        category = self.cat_var.get()

        if not all([name, price, stock, category]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        if not self._image_path:
            messagebox.showerror("Error", "Please upload a product image.")
            return

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products WHERE name=?", (name,))
        if cursor.fetchone():
            messagebox.showerror("Error", f"'{name}' already exists.")
            conn.close()
            return

        # Copy image to assets folder with sanitized filename
        ext      = os.path.splitext(self._image_path)[1].lower()
        filename = name.lower().replace(" ", "_").replace("/", "-") + ext
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "food @chizzlin")
        dest = os.path.join(assets_dir, filename)
        try:
            shutil.copy2(self._image_path, dest)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{e}")
            conn.close()
            return

        cursor.execute(
            "INSERT INTO products (id, name, price, stock, category) VALUES (?, ?, ?, ?, ?)",
            (self._get_next_id(), name, price, stock, category)
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", f"Product added successfully.\nImage saved as '{filename}'.")
        self.main_app.load_products()
        self.root.destroy()


# ── Edit Product Window ─────────────────────────────────────────

class EditProductWindow:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.root.title("Edit Product")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.grab_set()
        self.root.after(100, self.root.focus_force)
        self._image_path  = None
        self._preview_img = None

        w, h = 420, 620
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Banner
        banner = tk.Frame(root, bg=BROWN, height=38)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        tk.Label(banner, text="Edit Product", font=FONT_TITLE,
                 bg=BROWN, fg=YELLOW).pack(side="left", padx=14, pady=6)

        tk.Frame(root, bg=ACCENT, height=3).pack(fill="x")
        tk.Frame(root, bg=YELLOW, height=3).pack(fill="x")

        form = tk.Frame(root, bg=BG, padx=30, pady=16)
        form.pack(fill="both", expand=True)

        self.e_id       = entry_field(form, "Product ID  (required)")
        self.e_name     = entry_field(form, "New Name  (leave blank to keep)")
        self.e_price    = entry_field(form, "New Price  (leave blank to keep)")
        self.e_stock    = entry_field(form, "New Stock  (leave blank to keep)")

        # Category dropdown
        tk.Label(form, text="New Category  (leave blank to keep)", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))
        cat_border = tk.Frame(form, bg=ENTRY_BORDER, padx=1, pady=1)
        cat_border.pack(fill="x", pady=(2, 0))
        self.cat_var = tk.StringVar(value="")
        cat_menu = tk.OptionMenu(cat_border, self.cat_var, "", *CATEGORIES)
        cat_menu.config(bg=ENTRY_BG, fg=FG, activebackground=ACCENT,
                        activeforeground=FG, font=FONT_ENTRY,
                        relief="flat", bd=0, highlightthickness=0,
                        anchor="w", width=30)
        cat_menu["menu"].config(bg=ENTRY_BG, fg=FG, activebackground=ACCENT,
                                activeforeground=FG, font=FONT_ENTRY)
        cat_menu.pack(fill="x", padx=2, pady=2)

        # Image upload
        tk.Label(form, text="New Image  (leave blank to keep current)", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))

        img_row = tk.Frame(form, bg=BG)
        img_row.pack(fill="x", pady=(4, 0))

        self.preview_lbl = tk.Label(img_row, bg=ENTRY_BG, width=10, height=5,
                                    text="No image\nselected", font=FONT_SMALL, fg=SUBTLE,
                                    relief="flat",
                                    highlightbackground=ENTRY_BORDER, highlightthickness=1)
        self.preview_lbl.pack(side="left", padx=(0, 10))

        btn_col = tk.Frame(img_row, bg=BG)
        btn_col.pack(side="left", fill="y")
        styled_button(btn_col, "📁  Browse Image", self._browse_image,
                      bg=ACCENT, fg=BROWN, width=16).pack(pady=(0, 4))
        self.img_name_lbl = tk.Label(btn_col, text="", font=FONT_SMALL,
                                     bg=BG, fg=SUBTLE, wraplength=160, justify="left")
        self.img_name_lbl.pack(anchor="w")

        styled_button(form, "✎  Update Product", self._update, width=22).pack(pady=(16, 0), fill="x")

    def _browse_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select Product Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )
        if not path:
            return
        self._image_path = path
        self.img_name_lbl.config(text=os.path.basename(path))
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).resize((80, 60), Image.LANCZOS)
            self._preview_img = ImageTk.PhotoImage(img)
            self.preview_lbl.config(image=self._preview_img, text="")
        except Exception:
            self.preview_lbl.config(text="Preview\nunavailable")

    def _update(self):
        import shutil
        pid      = self.e_id.get().strip()
        name     = self.e_name.get().strip()
        price    = self.e_price.get().strip()
        stock    = self.e_stock.get().strip()
        category = self.cat_var.get()

        if not pid:
            messagebox.showerror("Error", "Product ID is required.")
            return

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, stock, category FROM products WHERE id=?", (pid,))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Not Found", f"No product with ID {pid}.")
            conn.close()
            return

        cur_name, cur_price, cur_stock, cur_cat = result
        new_name = name     or cur_name
        price    = price    or cur_price
        category = category or cur_cat

        if stock:
            try:
                stock = float(stock)
            except ValueError:
                messagebox.showerror("Error", "Stock must be a number.")
                conn.close()
                return
        else:
            stock = cur_stock

        # Handle optional image replacement
        if self._image_path:
            ext        = os.path.splitext(self._image_path)[1].lower()
            filename   = new_name.lower().replace(" ", "_").replace("/", "-") + ext
            assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "food @chizzlin")
            dest       = os.path.join(assets_dir, filename)
            try:
                shutil.copy2(self._image_path, dest)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image:\n{e}")
                conn.close()
                return

        cursor.execute(
            "UPDATE products SET name=?, price=?, stock=?, category=? WHERE id=?",
            (new_name, price, stock, category, pid)
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Product updated successfully.")
        self.main_app.load_products()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    ProductManagementSystem(root)
    root.mainloop()
