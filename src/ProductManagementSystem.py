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


class ProductManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Chizzling — Product Management")
        self.root.state("zoomed")
        self.root.configure(bg=BG)
        self.stocks = 30
        self.archive_window = None
        self.ingredients_window = None

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
            threshold = row[5] if len(row) > 5 else 30
            if stock <= threshold:
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
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a product from the table to edit.")
            return
        
        item = self.tree.item(selected[0])
        product_id = item['values'][0]
        EditProductWindow(tk.Toplevel(self.root), self, product_id)

    def OpenIngredientsTableWindow(self):
        if self.ingredients_window and tk.Toplevel.winfo_exists(self.ingredients_window):
            self.ingredients_window.focus_force()
            return
        toplevel = tk.Toplevel(self.root)
        self.ingredients_window = toplevel
        IngredientsTableWindow(toplevel)
        toplevel.protocol("WM_DELETE_WINDOW", lambda: self._close_window(toplevel, 'ingredients'))

    def OpenArchiveFeature(self):
        if self.archive_window and tk.Toplevel.winfo_exists(self.archive_window):
            self.archive_window.focus_force()
            return
        toplevel = tk.Toplevel(self.root)
        self.archive_window = toplevel
        ArchiveFeature(toplevel)
        toplevel.protocol("WM_DELETE_WINDOW", lambda: self._close_window(toplevel, 'archive'))

    def _close_window(self, window, window_type):
        if window_type == 'archive':
            self.archive_window = None
        elif window_type == 'ingredients':
            self.ingredients_window = None
        window.destroy()

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
        self._image_path = None
        self._preview_img = None
        self.ingredients_list = []

        w, h = 420, 650
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        banner = tk.Frame(root, bg=BROWN, height=38)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        tk.Label(banner, text="Add New Product", font=FONT_TITLE,
                 bg=BROWN, fg=YELLOW).pack(side="left", padx=14, pady=6)

        tk.Frame(root, bg=ACCENT, height=3).pack(fill="x")
        tk.Frame(root, bg=YELLOW, height=3).pack(fill="x")

        form = tk.Frame(root, bg=BG, padx=30, pady=16)
        form.pack(fill="both", expand=True)

        self.e_name = entry_field(form, "Product Name")
        self.e_price = entry_field(form, "Price (₱)")
        self.e_stock = entry_field(form, "Stock")
        self.e_threshold = entry_field(form, "Low Stock Threshold (default: 30)")

        tk.Label(form, text="Category", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))
        cat_border = tk.Frame(form, bg=ENTRY_BORDER, padx=1, pady=1)
        cat_border.pack(fill="x", pady=(2, 0))
        self.cat_var = tk.StringVar(value="")
        self.e_category = ttk.Combobox(cat_border, textvariable=self.cat_var,
                                       values=CATEGORIES, state="readonly", font=FONT_ENTRY)
        self.e_category.pack(fill="x", ipady=5, padx=4)
        self.e_category.bind("<FocusIn>", lambda e: cat_border.config(bg=ACCENT))
        self.e_category.bind("<FocusOut>", lambda e: cat_border.config(bg=ENTRY_BORDER))
        self.e_category.bind("<<ComboboxSelected>>", self._toggle_ingredients)
        self.e_category.bind("<MouseWheel>", lambda e: "break")

        tk.Label(form, text="Product Image  (required)", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))

        img_row = tk.Frame(form, bg=BG)
        img_row.pack(fill="x", pady=(4, 0))

        self.preview_lbl = tk.Label(img_row, bg=ENTRY_BG, width=10, height=5,
                                    text="No image", font=FONT_SMALL, fg=SUBTLE, relief="flat",
                                    highlightbackground=ENTRY_BORDER, highlightthickness=1)
        self.preview_lbl.pack(side="left", padx=(0, 10))

        btn_col = tk.Frame(img_row, bg=BG)
        btn_col.pack(side="left", fill="y")
        styled_button(btn_col, "📁  Browse Image", self._browse_image,
                      bg=ACCENT, fg=BROWN, width=16).pack(pady=(0, 4))
        self.img_name_lbl = tk.Label(btn_col, text="", font=FONT_SMALL,
                                     bg=BG, fg=SUBTLE, wraplength=160, justify="left")
        self.img_name_lbl.pack(anchor="w")

        self.ingredients_frame = tk.Frame(form, bg=BG)
        self._build_ingredients_section()

        self.add_btn = styled_button(form, "＋  Add Product", self._add, width=22)
        self.add_btn.pack(pady=(16, 0), fill="x")
        self._toggle_ingredients()

    def _build_ingredients_section(self):
        self.ing_label = tk.Label(self.ingredients_frame, text="Ingredients  (required for Meals)",
                                  font=FONT_LABEL, bg=BG, fg=BROWN, anchor="w")

        self.ing_list_frame = tk.Frame(self.ingredients_frame, bg=ENTRY_BG,
                                       relief="flat", highlightbackground=ENTRY_BORDER, highlightthickness=1)

        self.btn_row = tk.Frame(self.ingredients_frame, bg=BG)
        styled_button(self.btn_row, "＋ Add Ingredient", self._add_ingredient_dialog,
                      bg=ACCENT, fg=BROWN, width=18).pack(side="left", padx=(0, 4))
        styled_button(self.btn_row, "✎ New Ingredient", self._new_ingredient_dialog,
                      bg=SUBTLE, fg=YELLOW, width=18).pack(side="left")

    def _toggle_ingredients(self, *_):
        if self.cat_var.get() == "meals":
            self.ingredients_frame.pack(fill="x", pady=(8, 0), before=self.add_btn)
            self.ing_label.pack(fill="x", pady=(8, 0))
            self.ing_list_frame.pack(fill="x", pady=(4, 0))
            self.btn_row.pack(fill="x", pady=(6, 0))
            self._refresh_ingredient_list()
        else:
            self.ingredients_frame.pack_forget()
            self.ingredients_list.clear()

    def _refresh_ingredient_list(self):
        for w in self.ing_list_frame.winfo_children():
            w.destroy()
        if not self.ingredients_list:
            tk.Label(self.ing_list_frame, text="No ingredients added", font=FONT_SMALL,
                     bg=ENTRY_BG, fg=SUBTLE, pady=8).pack()
        else:
            for i, ing in enumerate(self.ingredients_list):
                row = tk.Frame(self.ing_list_frame, bg=ENTRY_BG)
                row.pack(fill="x", padx=4, pady=2)
                tk.Label(row, text=f"{ing['name']}: {ing['quantity']} {ing['unit']}",
                         font=FONT_SMALL, bg=ENTRY_BG, fg=FG, anchor="w").pack(side="left", fill="x", expand=True)
                tk.Button(row, text="✕", font=FONT_SMALL, bg="#c0392b", fg="white",
                          relief="flat", bd=0, cursor="hand2", width=3,
                          command=lambda idx=i: self._remove_ingredient(idx)).pack(side="right")

    def _remove_ingredient(self, idx):
        self.ingredients_list.pop(idx)
        self._refresh_ingredient_list()

    def _add_ingredient_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Ingredient")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.grab_set()
        dialog.geometry("350x280")

        form = tk.Frame(dialog, bg=BG, padx=20, pady=16)
        form.pack(fill="both", expand=True)

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, unit FROM ingredients ORDER BY name")
        ingredients_data = {r[0]: r[1] for r in cursor.fetchall()}
        conn.close()

        tk.Label(form, text="Select Ingredient", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(0, 2))
        ing_border = tk.Frame(form, bg=ENTRY_BORDER, padx=1, pady=1)
        ing_border.pack(fill="x")
        ing_var = tk.StringVar()
        ing_combo = ttk.Combobox(ing_border, textvariable=ing_var, values=list(ingredients_data.keys()),
                                 state="readonly", font=FONT_ENTRY)
        ing_combo.pack(fill="x", ipady=5, padx=4)

        e_qty = entry_field(form, "Quantity")
        
        tk.Label(form, text="Unit", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))
        unit_border = tk.Frame(form, bg=ENTRY_BORDER, padx=1, pady=1)
        unit_border.pack(fill="x", pady=(2, 0))
        unit_var = tk.StringVar()
        e_unit = tk.Entry(unit_border, font=FONT_ENTRY, bg="#e8e8e8", fg=FG,
                         relief="flat", bd=0, textvariable=unit_var, state="readonly")
        e_unit.pack(fill="x", ipady=6, padx=4)

        def on_ingredient_select(event):
            selected = ing_var.get()
            if selected in ingredients_data:
                unit_var.set(ingredients_data[selected])

        ing_combo.bind("<<ComboboxSelected>>", on_ingredient_select)

        def save():
            name = ing_var.get().strip()
            qty = e_qty.get().strip()
            unit = unit_var.get().strip()
            if not all([name, qty, unit]):
                messagebox.showerror("Error", "All fields are required.")
                return
            try:
                float(qty)
            except ValueError:
                messagebox.showerror("Error", "Quantity must be numeric.")
                return
            self.ingredients_list.append({"name": name, "quantity": qty, "unit": unit})
            self._refresh_ingredient_list()
            dialog.destroy()

        styled_button(form, "✓ Add", save, width=18).pack(pady=(12, 0), fill="x")

    def _new_ingredient_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("New Ingredient")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.grab_set()
        dialog.geometry("350x280")

        form = tk.Frame(dialog, bg=BG, padx=20, pady=16)
        form.pack(fill="both", expand=True)

        e_name = entry_field(form, "Ingredient Name")
        e_stock = entry_field(form, "Initial Stock")
        e_unit = entry_field(form, "Unit (e.g., grams, ml, pcs)")

        def save():
            name = e_name.get().strip()
            stock = e_stock.get().strip()
            unit = e_unit.get().strip()
            if not all([name, stock, unit]):
                messagebox.showerror("Error", "All fields are required.")
                return
            try:
                float(stock)
            except ValueError:
                messagebox.showerror("Error", "Stock must be numeric.")
                return
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ingredients WHERE name=?", (name,))
            if cursor.fetchone():
                messagebox.showerror("Error", f"'{name}' already exists.")
                conn.close()
                return
            cursor.execute("INSERT INTO ingredients (name, stock, unit) VALUES (?, ?, ?)",
                           (name, stock, unit))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"Ingredient '{name}' created.")
            dialog.destroy()

        styled_button(form, "✓ Create", save, width=18).pack(pady=(12, 0), fill="x")

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
        name = self.e_name.get().strip()
        price = self.e_price.get().strip()
        stock = self.e_stock.get().strip()
        threshold = self.e_threshold.get().strip() or "30"
        category = self.cat_var.get()

        if not all([name, price, stock, category]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            threshold = int(threshold)
        except ValueError:
            messagebox.showerror("Error", "Threshold must be a number.")
            return

        if category == "meals" and not self.ingredients_list:
            messagebox.showerror("Error", "Meal products must have at least one ingredient.")
            return

        for ing in self.ingredients_list:
            if not ing.get("quantity") or not ing.get("unit"):
                messagebox.showerror("Error", "All ingredients must have quantity and unit.")
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

        ext = os.path.splitext(self._image_path)[1].lower()
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
            "INSERT INTO products (id, name, price, stock, category, low_stock_threshold) VALUES (?, ?, ?, ?, ?, ?)",
            (self._get_next_id(), name, price, stock, category, threshold)
        )

        if category == "meals":
            for ing in self.ingredients_list:
                cursor.execute(
                    "INSERT INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
                    (name, ing["name"], ing["quantity"], ing["unit"])
                )

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", f"Product added successfully.\nImage saved as '{filename}'.")
        self.main_app.load_products()
        self.root.destroy()


# ── Edit Product Window ─────────────────────────────────────────

class EditProductWindow:
    def __init__(self, root, main_app, product_id):
        self.root = root
        self.main_app = main_app
        self.product_id = product_id
        self.root.title("Edit Product")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.grab_set()
        self.root.after(100, self.root.focus_force)
        self._image_path  = None
        self._preview_img = None
        self.ingredients_list = []
        self.current_product_name = None

        w, h = 800, 600
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        banner = tk.Frame(root, bg=BROWN, height=38)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        tk.Label(banner, text="Edit Product", font=FONT_TITLE,
                 bg=BROWN, fg=YELLOW).pack(side="left", padx=14, pady=6)

        tk.Frame(root, bg=ACCENT, height=3).pack(fill="x")
        tk.Frame(root, bg=YELLOW, height=3).pack(fill="x")

        main_container = tk.Frame(root, bg=BG)
        main_container.pack(fill="both", expand=True, padx=20, pady=16)
        
        # Left side - Product details
        left_frame = tk.Frame(main_container, bg=BG, width=150)
        left_frame.pack_propagate(False)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        form = tk.Frame(left_frame, bg=BG)
        form.pack(fill="both", expand=True)

        tk.Label(form, text=f"Product ID: {product_id}", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(0, 8))

        self.e_name     = entry_field(form, "Product Name")
        self.e_price    = entry_field(form, "Price (₱)")
        self.e_stock    = entry_field(form, "Stock")
        self.e_threshold = entry_field(form, "Low Stock Threshold")

        # Category dropdown
        tk.Label(form, text="Category", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))
        cat_border = tk.Frame(form, bg=ENTRY_BORDER, padx=1, pady=1)
        cat_border.pack(fill="x", pady=(2, 0))
        self.cat_var = tk.StringVar(value="")
        self.e_category = ttk.Combobox(cat_border, textvariable=self.cat_var,
                                       values=CATEGORIES, state="readonly",
                                       font=FONT_ENTRY, height=len(CATEGORIES))
        self.e_category.pack(fill="x", ipady=5, padx=4)
        self.e_category.bind("<FocusIn>",  lambda e: cat_border.config(bg=ACCENT))
        self.e_category.bind("<FocusOut>", lambda e: cat_border.config(bg=ENTRY_BORDER))
        self.e_category.bind("<<ComboboxSelected>>", self._on_category_change)
        self.e_category.bind("<MouseWheel>", lambda e: "break")

        # Image upload
        tk.Label(form, text="Product Image  (optional - leave to keep current)", font=FONT_LABEL,
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
        
        # Right side - Ingredients panel
        self.right_frame = tk.Frame(main_container, bg=BG, width=20)
        self.right_frame.pack_propagate(False)
        self.ingredients_frame = tk.Frame(self.right_frame, bg=BG)
        self.ingredients_frame.pack(fill="both", expand=True)
        self._build_ingredients_section()
        
        self._load_product_data()

    def _build_ingredients_section(self):
        tk.Label(self.ingredients_frame, text="Ingredients", font=FONT_TITLE,
                 bg=BG, fg=BROWN).pack(anchor="w", pady=(0, 4))
        tk.Frame(self.ingredients_frame, bg=YELLOW, height=3).pack(fill="x", pady=(0, 12))

        list_container = tk.Frame(self.ingredients_frame, bg=ENTRY_BORDER, padx=1, pady=1)
        list_container.pack(fill="both", expand=True, pady=(0, 10))
        
        ing_canvas = tk.Canvas(list_container, bg=ENTRY_BG, highlightthickness=0)
        ing_scrollbar = tk.Scrollbar(list_container, orient="vertical", command=ing_canvas.yview)
        self.ing_list_frame = tk.Frame(ing_canvas, bg=ENTRY_BG)
        
        self.ing_list_frame.bind("<Configure>", lambda e: ing_canvas.configure(scrollregion=ing_canvas.bbox("all")))
        ing_canvas.create_window((0, 0), window=self.ing_list_frame, anchor="nw", width=240)
        ing_canvas.configure(yscrollcommand=ing_scrollbar.set)
        
        ing_canvas.pack(side="left", fill="both", expand=True)
        ing_scrollbar.pack(side="right", fill="y")
        
        self.ing_list_container = list_container

        btn_frame = tk.Frame(self.ingredients_frame, bg=BG)
        btn_frame.pack(fill="x")
        styled_button(btn_frame, "＋ Add Ingredient", self._add_ingredient_dialog,
                      bg=ACCENT, fg=BROWN, width=14).pack(fill="x", pady=(0, 4))
        styled_button(btn_frame, "✎ New Ingredient", self._new_ingredient_dialog,
                      bg=SUBTLE, fg=YELLOW, width=14).pack(fill="x")

    def _on_category_change(self, *_):
        if self.cat_var.get() == "meals":
            self._show_ingredients_panel()
        else:
            self._hide_ingredients_panel()

    def _show_ingredients_panel(self):
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self._refresh_ingredient_list()

    def _hide_ingredients_panel(self):
        self.right_frame.pack_forget()

    def _load_product_data(self):
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]
        has_threshold = "low_stock_threshold" in columns
        
        if has_threshold:
            cursor.execute("SELECT name, price, stock, category, low_stock_threshold FROM products WHERE id=?", (self.product_id,))
        else:
            cursor.execute("SELECT name, price, stock, category FROM products WHERE id=?", (self.product_id,))
        
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", f"Product with ID {self.product_id} not found.")
            conn.close()
            self.root.destroy()
            return

        if has_threshold:
            cur_name, cur_price, cur_stock, cur_cat, cur_threshold = result
        else:
            cur_name, cur_price, cur_stock, cur_cat = result
            cur_threshold = 30
        
        self.current_product_name = cur_name
        
        self.e_name.insert(0, cur_name)
        self.e_price.insert(0, cur_price)
        self.e_stock.insert(0, cur_stock)
        self.e_threshold.insert(0, cur_threshold)
        self.cat_var.set(cur_cat)

        self.ingredients_list.clear()
        if cur_cat == "meals":
            cursor.execute("SELECT ingredient_name, quantity, unit FROM recipe_ingredients WHERE product_name=?", (cur_name,))
            for row in cursor.fetchall():
                self.ingredients_list.append({"name": row[0], "quantity": row[1], "unit": row[2]})
            self._show_ingredients_panel()
        else:
            self._hide_ingredients_panel()

        conn.close()

    def _refresh_ingredient_list(self):
        for w in self.ing_list_frame.winfo_children():
            w.destroy()
        if not self.ingredients_list:
            tk.Label(self.ing_list_frame, text="No ingredients added", font=FONT_SMALL,
                     bg=ENTRY_BG, fg=SUBTLE, pady=8).pack()
        else:
            for i, ing in enumerate(self.ingredients_list):
                row = tk.Frame(self.ing_list_frame, bg=ENTRY_BG)
                row.pack(fill="x", padx=4, pady=2)
                tk.Label(row, text=f"{ing['name']}: {ing['quantity']} {ing['unit']}",
                         font=FONT_SMALL, bg=ENTRY_BG, fg=FG, anchor="w").pack(side="left", fill="x", expand=True)
                tk.Button(row, text="✕", font=FONT_SMALL, bg="#c0392b", fg="white",
                          relief="flat", bd=0, cursor="hand2", width=3,
                          command=lambda idx=i: self._remove_ingredient(idx)).pack(side="right")

    def _remove_ingredient(self, idx):
        self.ingredients_list.pop(idx)
        self._refresh_ingredient_list()

    def _add_ingredient_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Ingredient")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.grab_set()
        dialog.geometry("350x280")

        form = tk.Frame(dialog, bg=BG, padx=20, pady=16)
        form.pack(fill="both", expand=True)

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, unit FROM ingredients ORDER BY name")
        ingredients_data = {r[0]: r[1] for r in cursor.fetchall()}
        conn.close()

        tk.Label(form, text="Select Ingredient", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(0, 2))
        ing_border = tk.Frame(form, bg=ENTRY_BORDER, padx=1, pady=1)
        ing_border.pack(fill="x")
        ing_var = tk.StringVar()
        ing_combo = ttk.Combobox(ing_border, textvariable=ing_var, values=list(ingredients_data.keys()),
                                 state="readonly", font=FONT_ENTRY)
        ing_combo.pack(fill="x", ipady=5, padx=4)

        e_qty = entry_field(form, "Quantity")
        
        tk.Label(form, text="Unit", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))
        unit_border = tk.Frame(form, bg=ENTRY_BORDER, padx=1, pady=1)
        unit_border.pack(fill="x", pady=(2, 0))
        unit_var = tk.StringVar()
        e_unit = tk.Entry(unit_border, font=FONT_ENTRY, bg="#e8e8e8", fg=FG,
                         relief="flat", bd=0, textvariable=unit_var, state="readonly")
        e_unit.pack(fill="x", ipady=6, padx=4)

        def on_ingredient_select(event):
            selected = ing_var.get()
            if selected in ingredients_data:
                unit_var.set(ingredients_data[selected])

        ing_combo.bind("<<ComboboxSelected>>", on_ingredient_select)

        def save():
            name = ing_var.get().strip()
            qty = e_qty.get().strip()
            unit = unit_var.get().strip()
            if not all([name, qty, unit]):
                messagebox.showerror("Error", "All fields are required.")
                return
            try:
                float(qty)
            except ValueError:
                messagebox.showerror("Error", "Quantity must be numeric.")
                return
            self.ingredients_list.append({"name": name, "quantity": qty, "unit": unit})
            self._refresh_ingredient_list()
            dialog.destroy()

        styled_button(form, "✓ Add", save, width=18).pack(pady=(12, 0), fill="x")

    def _new_ingredient_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("New Ingredient")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.grab_set()
        dialog.geometry("350x280")

        form = tk.Frame(dialog, bg=BG, padx=20, pady=16)
        form.pack(fill="both", expand=True)

        e_name = entry_field(form, "Ingredient Name")
        e_stock = entry_field(form, "Initial Stock")
        e_unit = entry_field(form, "Unit (e.g., grams, ml, pcs)")

        def save():
            name = e_name.get().strip()
            stock = e_stock.get().strip()
            unit = e_unit.get().strip()
            if not all([name, stock, unit]):
                messagebox.showerror("Error", "All fields are required.")
                return
            try:
                float(stock)
            except ValueError:
                messagebox.showerror("Error", "Stock must be numeric.")
                return
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ingredients WHERE name=?", (name,))
            if cursor.fetchone():
                messagebox.showerror("Error", f"'{name}' already exists.")
                conn.close()
                return
            cursor.execute("INSERT INTO ingredients (name, stock, unit) VALUES (?, ?, ?)",
                           (name, stock, unit))
            conn.commit()
            conn.close()
            from tkinter.messagebox import showinfo
            showinfo("Success", f"Ingredient '{name}' created.")
            dialog.destroy()

        styled_button(form, "✓ Create", save, width=18).pack(pady=(12, 0), fill="x")

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
        name     = self.e_name.get().strip()
        price    = self.e_price.get().strip()
        stock    = self.e_stock.get().strip()
        threshold = self.e_threshold.get().strip()
        category = self.cat_var.get()

        if not all([name, price, stock, threshold, category]):
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            price = float(price)
            stock = float(stock)
            threshold = int(threshold)
        except ValueError:
            messagebox.showerror("Error", "Price, stock, and threshold must be valid numbers.")
            return

        if category == "meals" and not self.ingredients_list:
            messagebox.showerror("Error", "Meal products must have at least one ingredient.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        if self._image_path:
            ext        = os.path.splitext(self._image_path)[1].lower()
            filename   = name.lower().replace(" ", "_").replace("/", "-") + ext
            assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "food @chizzlin")
            dest       = os.path.join(assets_dir, filename)
            try:
                shutil.copy2(self._image_path, dest)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image:\n{e}")
                conn.close()
                return

        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]
        has_threshold = "low_stock_threshold" in columns
        
        if has_threshold:
            cursor.execute(
                "UPDATE products SET name=?, price=?, stock=?, category=?, low_stock_threshold=? WHERE id=?",
                (name, price, stock, category, threshold, self.product_id)
            )
        else:
            cursor.execute(
                "UPDATE products SET name=?, price=?, stock=?, category=? WHERE id=?",
                (name, price, stock, category, self.product_id)
            )

        if category == "meals":
            cursor.execute("DELETE FROM recipe_ingredients WHERE product_name=?", (self.current_product_name,))
            for ing in self.ingredients_list:
                cursor.execute(
                    "INSERT INTO recipe_ingredients (product_name, ingredient_name, quantity, unit) VALUES (?, ?, ?, ?)",
                    (name, ing["name"], ing["quantity"], ing["unit"])
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
