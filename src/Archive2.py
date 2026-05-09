import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox
from database_setup import connect_db

# ── Color palette (matches system) ──────────────────────────
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


class ArchiveFeature2:
    def __init__(self, root):
        self.root = root
        self.root.title("Chizzling — Ingredients Archive")
        self.root.configure(bg=BG)
        
        w, h = 1000, 650
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.resizable(False, False)

        self._build_ui()
        self.load_products()
        self.root.after(100, self.root.focus_force)

    def _build_ui(self):
        # Top banner
        banner = tk.Frame(self.root, bg=BROWN, height=42)
        banner.pack(fill="x", side="top")
        banner.pack_propagate(False)

        tk.Label(banner, text="Chizzling POS  ·  Ingredients Archive",
                 font=FONT_TITLE, bg=BROWN, fg=YELLOW).pack(side="left", padx=16, pady=8)

        tk.Frame(self.root, bg=ACCENT, height=4).pack(fill="x")
        tk.Frame(self.root, bg=YELLOW, height=4).pack(fill="x")

        # Body
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        # Right — controls (pack first)
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
        style.configure("Archive.Treeview",
                        background=ENTRY_BG, fieldbackground=ENTRY_BG,
                        foreground=FG, font=FONT_ENTRY, rowheight=28)
        style.configure("Archive.Treeview.Heading",
                        background=BROWN, foreground=YELLOW,
                        font=FONT_LABEL, relief="flat")
        style.map("Archive.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", BROWN)])

        tree_frame = tk.Frame(parent, bg=BROWN, padx=1, pady=1)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, style="Archive.Treeview",
                                 selectmode="browse")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _build_controls(self, parent):
        tk.Label(parent, text="Actions", font=FONT_TITLE,
                 bg=BG, fg=BROWN).pack(anchor="w", pady=(0, 4))
        tk.Frame(parent, bg=YELLOW, height=3).pack(fill="x", pady=(0, 12))

        tk.Label(parent, text="Unarchive by ID or Name",
                 font=FONT_SMALL, bg=BG, fg=SUBTLE).pack(anchor="w")

        unarch_border = tk.Frame(parent, bg=ENTRY_BORDER, padx=1, pady=1)
        unarch_border.pack(fill="x", pady=(2, 6))
        self.unarchive_entry = tk.Entry(unarch_border, font=FONT_ENTRY,
                                        bg=ENTRY_BG, fg=FG, relief="flat", bd=0)
        self.unarchive_entry.pack(fill="x", ipady=6, padx=4)
        self.unarchive_entry.bind("<FocusIn>",  lambda e: unarch_border.config(bg=ACCENT))
        self.unarchive_entry.bind("<FocusOut>", lambda e: unarch_border.config(bg=ENTRY_BORDER))

        styled_button(parent, "↩  Unarchive",
                      self.unarchive_products,
                      bg=ACCENT, fg=BROWN).pack(fill="x", pady=4)

        tk.Frame(parent, bg=YELLOW, height=2).pack(fill="x", pady=10)

        tk.Label(parent, text="Delete by ID or Name",
                 font=FONT_SMALL, bg=BG, fg=SUBTLE).pack(anchor="w")

        del_border = tk.Frame(parent, bg=ENTRY_BORDER, padx=1, pady=1)
        del_border.pack(fill="x", pady=(2, 6))
        self.delete_entry = tk.Entry(del_border, font=FONT_ENTRY,
                                     bg=ENTRY_BG, fg=FG, relief="flat", bd=0)
        self.delete_entry.pack(fill="x", ipady=6, padx=4)
        self.delete_entry.bind("<FocusIn>",  lambda e: del_border.config(bg=ACCENT))
        self.delete_entry.bind("<FocusOut>", lambda e: del_border.config(bg=ENTRY_BORDER))

        styled_button(parent, "🗑  Delete Permanently",
                      self.delete_product,
                      bg="#c0392b", fg=YELLOW).pack(fill="x", pady=4)

    def load_products(self):
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ingredients_archive")
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
        keyword = self.search_var.get()

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM ingredients_archive
        WHERE id LIKE ? OR name LIKE ?
        """, ('%' + keyword + '%', '%' + keyword + '%'))

        rows = cursor.fetchall()

        self.tree.delete(*self.tree.get_children())

        for row in rows:
            self.tree.insert("", tk.END, values=row)

        conn.close()

    def delete_product(self):
        keyword = self.delete_entry.get().strip()

        if not keyword:
            messagebox.showwarning("Warning", "Enter Ingredient ID or Name", parent=self.root)
            return
        
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ingredients_archive WHERE id=? OR name=?", (keyword, keyword))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "Ingredient not found", parent=self.root)
            conn.close()
            return
        
        confirm = messagebox.askyesno("Confirm", f"Delete '{result[1]}' permanently?", parent=self.root)
        if not confirm:
            conn.close()
            return
        
        cursor.execute("DELETE FROM ingredients_archive WHERE id=? OR name=?", (keyword, keyword))

        conn.commit()
        conn.close()

        self.delete_entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Deleted permanently", parent=self.root)
        self.load_products()

    def unarchive_products(self):
        keyword = self.unarchive_entry.get().strip()

        if not keyword:
            messagebox.showwarning("Warning", "Enter Ingredient ID or Name", parent=self.root)
            return
        
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ingredients_archive WHERE id=? OR name=?", (keyword, keyword))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "Ingredient not found", parent=self.root)
            conn.close()
            return
        
        confirm = messagebox.askyesno("Confirm", f"Unarchive '{result[1]}'?", parent=self.root)
        if not confirm:
            conn.close()
            return
        
        cursor.execute("""
        INSERT INTO ingredients (name, stock, unit)
        SELECT name, stock, unit FROM ingredients_archive WHERE id=? OR name=?
        """, (keyword, keyword))

        cursor.execute("DELETE FROM ingredients_archive WHERE id=? OR name=?", (keyword, keyword))

        conn.commit()
        conn.close()

        self.unarchive_entry.delete(0, tk.END)
        messagebox.showinfo("Success", "Ingredient unarchived successfully", parent=self.root)
        self.load_products()


# RUN
if __name__ == "__main__":
    root = tk.Tk()
    app = ArchiveFeature2(root)
    root.mainloop()