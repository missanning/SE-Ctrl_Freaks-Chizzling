import tkinter as tk
from tkinter import ttk, messagebox
from database_setup import connect_db

try:
    from Archive2 import ArchiveFeature2
    ARCHIVE2_AVAILABLE = True
except ImportError:
    ARCHIVE2_AVAILABLE = False

# ── Color palette (matches LoginPage) ──────────────────────────
BG           = "#ffffff"
ACCENT       = "#f5a623"
YELLOW       = "#ffd966"
BROWN        = "#7a3b10"
FG           = "#3b1f0a"
SUBTLE       = "#7a3b10"
ENTRY_BG     = "#fff8ee"
ENTRY_BORDER = "#f5a623"

FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_ENTRY = ("Segoe UI", 10)
FONT_BTN   = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)


def styled_button(parent, text, command, bg=BROWN, fg=YELLOW, width=20):
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=ACCENT, activeforeground=BROWN,
        font=FONT_BTN, relief="flat", bd=0, padx=10, pady=6,
        cursor="hand2", width=width
    )


def entry_field(parent, label_text):
    tk.Label(parent, text=label_text, font=FONT_LABEL,
             bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(8, 0))
    border = tk.Frame(parent, bg=ENTRY_BORDER, padx=1, pady=1)
    border.pack(fill="x", pady=(2, 0))
    e = tk.Entry(border, font=FONT_ENTRY, bg=ENTRY_BG, fg=FG,
                 relief="flat", bd=0)
    e.pack(fill="x", ipady=6, padx=4)
    e.bind("<FocusIn>",  lambda ev: border.config(bg=ACCENT))
    e.bind("<FocusOut>", lambda ev: border.config(bg=ENTRY_BORDER))
    return e


class IngredientsTableWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Chizzling — Ingredients Table")
        self.root.configure(bg=BG)
        
        # Center and size window
        w, h = 1000, 650
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.resizable(False, False)

        # Low stock thresholds
        self.low_limits = {
            "grams": 5000, "pcs": 200,
            "tsp": 500, "slices": 500, "ml": 1500
        }

        self._build_ui()
        self.load_products()
        self.root.after(100, self.root.focus_force)



    # ── UI Layout ───────────────────────────────────────────────

    def _build_ui(self):
        # Top banner
        banner = tk.Frame(self.root, bg=BROWN, height=42)
        banner.pack(fill="x", side="top")
        banner.pack_propagate(False)

        tk.Label(banner, text="Chizzling POS  ·  Ingredients Table",
                 font=FONT_TITLE, bg=BROWN, fg=YELLOW).pack(side="left", padx=16, pady=8)

        tk.Frame(self.root, bg=ACCENT, height=4).pack(fill="x")
        tk.Frame(self.root, bg=YELLOW, height=4).pack(fill="x")

        # Body
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        # Right — controls (pack first to maintain position)
        right = tk.Frame(body, bg=BG, width=220)
        right.pack(side="right", fill="y", padx=(16, 0))
        right.pack_propagate(False)
        self._build_controls(right)

        # Left — table
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)
        self._build_table(left)

        # Bottom strip
        tk.Frame(self.root, bg=YELLOW, height=4).pack(fill="x", side="bottom")
        tk.Frame(self.root, bg=ACCENT, height=4).pack(fill="x", side="bottom")
        tk.Frame(self.root, bg=BROWN, height=8).pack(fill="x", side="bottom")

    def _build_table(self, parent):
        # Search row
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
        style.configure("Ingr.Treeview",
                        background=ENTRY_BG, fieldbackground=ENTRY_BG,
                        foreground=FG, font=FONT_ENTRY, rowheight=28)
        style.configure("Ingr.Treeview.Heading",
                        background=BROWN, foreground=YELLOW,
                        font=FONT_LABEL, relief="flat")
        style.map("Ingr.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", BROWN)])

        tree_frame = tk.Frame(parent, bg=BROWN, padx=1, pady=1)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, style="Ingr.Treeview",
                                 selectmode="browse")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _build_controls(self, parent):
        tk.Label(parent, text="Actions", font=FONT_TITLE,
                 bg=BG, fg=BROWN).pack(anchor="w", pady=(0, 4))
        tk.Frame(parent, bg=YELLOW, height=3).pack(fill="x", pady=(0, 12))

        styled_button(parent, "＋  Add Ingredient",
                      self.OpenAddProductWindow).pack(fill="x", pady=4)
        styled_button(parent, "✎  Edit Ingredient",
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

        styled_button(parent, "📦  Archive Ingredient",
                      self.archive_products,
                      bg="#a0522d", fg=YELLOW).pack(fill="x", pady=4)

        styled_button(parent, "🗂  View Archive",
                      self.OpenArchiveFeature,
                      bg=SUBTLE, fg=YELLOW).pack(fill="x", pady=4)

    # ── Data ────────────────────────────────────────────────────

    def load_products(self, *_):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ingredients")
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        conn.close()

        self.tree.delete(*self.tree.get_children())
        
        if not self.tree["columns"]:
            self.tree["columns"] = col_names
            self.tree["show"] = "headings"
            for col in col_names:
                self.tree.heading(col, text=col.capitalize())
                self.tree.column(col, width=120, anchor="center", minwidth=120)

        low_items = []
        for row in rows:
            stock = row[2]
            threshold = row[4] if len(row) > 4 else 0
            if threshold > 0 and stock <= threshold:
                self.tree.insert("", tk.END, values=row, tags=("low",))
                low_items.append(row[1])
            else:
                self.tree.insert("", tk.END, values=row)

        self.tree.tag_configure("low", background="#ffe0e0", foreground="#c0392b")

        if low_items:
            self.root.after(100, lambda: self._show_low_stock_alert(low_items))

    def _show_low_stock_alert(self, low_items):
        messagebox.showwarning("Low Stock Alert",
                               "Low stock items:\n• " + "\n• ".join(low_items),
                               parent=self.root)
        self.root.lift()
        self.root.focus_force()

    def search_product(self):
        keyword = self.search_var.get()
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ingredients WHERE id LIKE ? OR name LIKE ?",
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
            messagebox.showwarning("Archive", "Enter an ingredient ID or name.", parent=self.root)
            return

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ingredients WHERE id=? OR name=?", (keyword, keyword))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Not Found", "Ingredient not found.", parent=self.root)
            conn.close()
            return

        if not messagebox.askyesno("Confirm Archive", f"Archive '{result[1]}'?", parent=self.root):
            conn.close()
            return

        cursor.execute("""
            INSERT INTO ingredients_archive (name, stock, unit)
            SELECT name, stock, unit FROM ingredients WHERE id=? OR name=?
        """, (keyword, keyword))
        cursor.execute("DELETE FROM ingredients WHERE id=? OR name=?", (keyword, keyword))
        conn.commit()
        conn.close()

        self.archive_entry.delete(0, tk.END)
        messagebox.showinfo("Archived", "Ingredient archived successfully.", parent=self.root)
        self.load_products()
        self.root.lift()
        self.root.focus_force()

    # ── Navigation ──────────────────────────────────────────────

    def OpenAddProductWindow(self):
        AddIngredientWindow(tk.Toplevel(self.root), self)

    def OpenEditProductWindow(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an ingredient from the table to edit.", parent=self.root)
            return
        
        item = self.tree.item(selected[0])
        ingredient_id = item['values'][0]
        EditIngredientWindow(tk.Toplevel(self.root), self, ingredient_id)

    def OpenArchiveFeature(self):
        if ARCHIVE2_AVAILABLE:
            ArchiveFeature2(tk.Toplevel(self.root))
        else:
            messagebox.showwarning("Unavailable", "Archive2 module not found.", parent=self.root)


# ── Add Ingredient Window ───────────────────────────────────────

class AddIngredientWindow:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.root.title("Add Ingredient")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.grab_set()
        self.root.after(100, self.root.focus_force)
        self.root.bind_all("<Button-1>", lambda e: e.widget.focus_set() if isinstance(e.widget, tk.Entry) else None)

        w, h = 380, 400
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        banner = tk.Frame(root, bg=BROWN, height=38)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        tk.Label(banner, text="Add New Ingredient", font=FONT_TITLE,
                 bg=BROWN, fg=YELLOW).pack(side="left", padx=14, pady=6)

        tk.Frame(root, bg=ACCENT, height=3).pack(fill="x")
        tk.Frame(root, bg=YELLOW, height=3).pack(fill="x")

        form = tk.Frame(root, bg=BG, padx=30, pady=20)
        form.pack(fill="both", expand=True)

        self.e_name  = entry_field(form, "Ingredient Name")
        self.e_stock = entry_field(form, "Stock")
        self.e_unit  = entry_field(form, "Unit  (grams / pcs / tsp / slices / ml)")
        self.e_threshold = entry_field(form, "Low Stock Threshold")

        styled_button(form, "＋  Add Ingredient", self._add, width=22).pack(pady=(18, 0), fill="x")

    def _add(self):
        name  = self.e_name.get().strip()
        stock = self.e_stock.get().strip()
        unit  = self.e_unit.get().strip()
        threshold = self.e_threshold.get().strip() or "0"

        if not all([name, stock, unit]):
            messagebox.showerror("Error", "Please fill in all fields.", parent=self.root)
            return
        
        try:
            threshold = float(threshold)
        except ValueError:
            messagebox.showerror("Error", "Threshold must be a number.", parent=self.root)
            return

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ingredients WHERE name=?", (name,))
        if cursor.fetchone():
            messagebox.showerror("Error", f"'{name}' already exists.", parent=self.root)
            conn.close()
            return

        cursor.execute("INSERT INTO ingredients (name, stock, unit, low_stock_threshold) VALUES (?, ?, ?, ?)",
                       (name, stock, unit, threshold))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Ingredient added successfully.", parent=self.root)
        self.main_app.load_products()
        self.root.destroy()


# ── Edit Ingredient Window ──────────────────────────────────────

class EditIngredientWindow:
    def __init__(self, root, main_app, ingredient_id):
        self.root = root
        self.main_app = main_app
        self.ingredient_id = ingredient_id
        self.root.title("Edit Ingredient")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.grab_set()
        self.root.after(100, self.root.focus_force)
        self.root.bind_all("<Button-1>", lambda e: e.widget.focus_set() if isinstance(e.widget, tk.Entry) else None)

        w, h = 380, 450
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        banner = tk.Frame(root, bg=BROWN, height=38)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        tk.Label(banner, text="Edit Ingredient", font=FONT_TITLE,
                 bg=BROWN, fg=YELLOW).pack(side="left", padx=14, pady=6)

        tk.Frame(root, bg=ACCENT, height=3).pack(fill="x")
        tk.Frame(root, bg=YELLOW, height=3).pack(fill="x")

        form = tk.Frame(root, bg=BG, padx=30, pady=20)
        form.pack(fill="both", expand=True)

        tk.Label(form, text=f"Ingredient ID: {ingredient_id}", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(0, 8))

        self.e_name  = entry_field(form, "Ingredient Name")
        self.e_stock = entry_field(form, "Stock")
        self.e_unit  = entry_field(form, "Unit  (grams / pcs / tsp / slices / ml)")
        self.e_threshold = entry_field(form, "Low Stock Threshold")

        styled_button(form, "✎  Update Ingredient", self._update, width=22).pack(pady=(18, 0), fill="x")
        
        self._load_ingredient_data()

    def _load_ingredient_data(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, stock, unit, low_stock_threshold FROM ingredients WHERE id=?", (self.ingredient_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            messagebox.showerror("Error", f"Ingredient with ID {self.ingredient_id} not found.", parent=self.root)
            self.root.destroy()
            return

        cur_name, cur_stock, cur_unit, cur_threshold = result
        
        self.e_name.insert(0, cur_name)
        self.e_stock.insert(0, cur_stock)
        self.e_unit.insert(0, cur_unit)
        self.e_threshold.insert(0, cur_threshold if cur_threshold else "0")

    def _update(self):
        name   = self.e_name.get().strip()
        stock  = self.e_stock.get().strip()
        unit   = self.e_unit.get().strip()
        threshold = self.e_threshold.get().strip()

        if not all([name, stock, unit, threshold]):
            messagebox.showerror("Error", "All fields are required.", parent=self.root)
            return

        try:
            stock = float(stock)
            threshold = float(threshold)
        except ValueError:
            messagebox.showerror("Error", "Stock and threshold must be valid numbers.", parent=self.root)
            return

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ingredients SET name=?, stock=?, unit=?, low_stock_threshold=? WHERE id=?",
            (name, stock, unit, threshold, self.ingredient_id)
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Ingredient updated successfully.", parent=self.root)
        self.main_app.load_products()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    IngredientsTableWindow(root)
    root.mainloop()
