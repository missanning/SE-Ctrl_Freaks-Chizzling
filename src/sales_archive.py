import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from dashboard_db import connect_db

BG      = "#FFF8EE"
SIDEBAR = "#7a3b10"
ACCENT  = "#f5a623"
YELLOW  = "#ffd966"
FG_DARK = "#3b1f0a"
FG_LIGHT = "#fff3e0"
CONTENT = "#ffffff"
ROW_ALT = "#fff3e0"
FONT    = "Segoe UI"


def _ensure_archive_tables():
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS transaction_archive (
            id INTEGER PRIMARY KEY,
            total REAL, payment REAL, change REAL, date TIMESTAMP,
            archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS transaction_items_archive (
            id INTEGER PRIMARY KEY,
            transaction_id INTEGER, product_id INTEGER,
            quantity INTEGER, subtotal REAL
        )""")
    conn.close()


def _month_range(year, month):
    """Return (first_day, last_day) strings for a given month."""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    return (f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last_day:02d}")


MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


class SalesArchive:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Archive — Chizzling POS")
        self.root.configure(bg=BG)
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"1200x720+{(sw-1200)//2}+{(sh-720)//2}")
        _ensure_archive_tables()
        self._build_ui()
        self._load_archived(auto=True)

    def _round_btn(self, parent, text, cmd, bg, fg, width=160, height=36):
        c = tk.Canvas(parent, width=width, height=height, bg=parent.cget("bg"),
                      highlightthickness=0, cursor="hand2")
        c.pack(side="left", padx=6)
        r = 12
        def _draw(hover=False, c=c, bg=bg):
            c.delete("all")
            w, h = width, height
            col = self._darken(bg) if hover else bg
            c.create_polygon(r,0, w-r,0, w,0, w,r, w,h-r, w,h,
                             w-r,h, r,h, 0,h, 0,h-r, 0,r, 0,0,
                             smooth=True, fill=col, outline=col)
            c.create_text(w//2, h//2, text=text, font=(FONT, 11, "bold"), fill=fg)
        _draw()
        c.bind("<Button-1>",  lambda e: cmd())
        c.bind("<Enter>",     lambda e: _draw(True))
        c.bind("<Leave>",     lambda e: _draw(False))
        return c

    def _darken(self, hex_color):
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
        r, g, b = max(0,r-30), max(0,g-30), max(0,b-30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=SIDEBAR, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🗂  Sales Archive",
                 font=(FONT, 14, "bold"), bg=SIDEBAR, fg=YELLOW).pack(side="left", padx=20, pady=10)
        tk.Frame(self.root, bg=ACCENT, height=3).pack(fill="x")
        tk.Frame(self.root, bg=YELLOW, height=2).pack(fill="x")

        now = datetime.now()
        current_year = now.year

        # Summary label
        self.summary_var = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.summary_var,
                 font=(FONT, 11), bg=BG, fg=FG_DARK).pack(anchor="w", padx=24, pady=(6, 0))

        # ── Row 1: Archive ────────────────────────────────────────────────────
        row1 = tk.Frame(self.root, bg=BG)
        row1.pack(fill="x", padx=24, pady=(14, 4))
        tk.Label(row1, text="Archive Month:", font=(FONT, 11, "bold"),
                 bg=BG, fg=FG_DARK).pack(side="left", padx=(0, 8))
        self.month_var = tk.StringVar(value=MONTHS[now.month - 2] if now.month > 1 else "December")
        ttk.Combobox(row1, textvariable=self.month_var, width=13,
                     values=MONTHS, state="readonly", font=(FONT, 11)).pack(side="left")
        self.year_var = tk.StringVar(value=str(current_year if now.month > 1 else current_year - 1))
        ttk.Combobox(row1, textvariable=self.year_var, width=7,
                     values=[str(y) for y in range(current_year - 5, current_year + 1)],
                     state="readonly", font=(FONT, 11)).pack(side="left", padx=(6, 16))
        self._round_btn(row1, "🗂  Archive Month", self._archive_sales, SIDEBAR, FG_LIGHT, 180)

        # ── Row 2: Restore / Delete / View ───────────────────────────────────
        row2 = tk.Frame(self.root, bg=BG)
        row2.pack(fill="x", padx=24, pady=(4, 8))
        tk.Label(row2, text="Restore / Delete:", font=(FONT, 11, "bold"),
                 bg=BG, fg=FG_DARK).pack(side="left", padx=(0, 8))
        self.restore_month_var = tk.StringVar(value=MONTHS[now.month - 2] if now.month > 1 else "December")
        ttk.Combobox(row2, textvariable=self.restore_month_var, width=13,
                     values=MONTHS, state="readonly", font=(FONT, 11)).pack(side="left")
        self.restore_year_var = tk.StringVar(value=str(current_year if now.month > 1 else current_year - 1))
        ttk.Combobox(row2, textvariable=self.restore_year_var, width=7,
                     values=[str(y) for y in range(current_year - 5, current_year + 1)],
                     state="readonly", font=(FONT, 11)).pack(side="left", padx=(6, 16))
        self._round_btn(row2, "↩  Restore",     self._restore_by_month, ACCENT,   FG_DARK,  140)
        self._round_btn(row2, "🗑  Delete",      self._delete_by_month,  "#8b0000", FG_LIGHT, 130)

        tk.Frame(row2, bg=ACCENT, width=2, height=30).pack(side="left", padx=16)

        tk.Label(row2, text="View:", font=(FONT, 11, "bold"),
                 bg=BG, fg=FG_DARK).pack(side="left", padx=(0, 8))
        self.view_month_var = tk.StringVar(value="All")
        ttk.Combobox(row2, textvariable=self.view_month_var, width=13,
                     values=["All"] + MONTHS, state="readonly",
                     font=(FONT, 11)).pack(side="left")
        self.view_year_var = tk.StringVar(value=str(current_year))
        ttk.Combobox(row2, textvariable=self.view_year_var, width=7,
                     values=[str(y) for y in range(current_year - 5, current_year + 1)],
                     state="readonly", font=(FONT, 11)).pack(side="left", padx=(6, 8))
        self._round_btn(row2, "🔍  View", self._load_archived, YELLOW, FG_DARK, 120)

        # Table
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Arc.Treeview",
                         background=CONTENT, fieldbackground=CONTENT,
                         foreground=FG_DARK, font=(FONT, 11), rowheight=30)
        style.configure("Arc.Treeview.Heading",
                         background=SIDEBAR, foreground=FG_LIGHT,
                         font=(FONT, 11, "bold"), relief="flat")
        style.map("Arc.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", FG_DARK)])

        table_frame = tk.Frame(self.root, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        cols = ("ID", "Date", "Total", "Payment", "Change", "Archived On")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                 selectmode="extended", style="Arc.Treeview")
        self.tree.tag_configure("odd",  background=CONTENT)
        self.tree.tag_configure("even", background=ROW_ALT)

        widths = [60, 160, 110, 110, 110, 180]
        anchors = ["center", "center", "e", "e", "e", "center"]
        for col, w, anc in zip(cols, widths, anchors):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anc)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # Bottom strip
        tk.Frame(self.root, bg=ACCENT, height=3).pack(fill="x", side="bottom")
        tk.Frame(self.root, bg=SIDEBAR, height=8).pack(fill="x", side="bottom")

    def _load_archived(self, auto=False):
        self.tree.delete(*self.tree.get_children())
        conn = connect_db()
        with conn:
            cur = conn.cursor()
            view_month = self.view_month_var.get()
            if view_month == "All":
                cur.execute("""SELECT id, date, total, payment, change, archived_date
                               FROM transaction_archive ORDER BY date DESC""")
            else:
                month = MONTHS.index(view_month) + 1
                year = int(self.view_year_var.get())
                date_from, date_to = _month_range(year, month)
                cur.execute("""SELECT id, date, total, payment, change, archived_date
                               FROM transaction_archive
                               WHERE DATE(date) BETWEEN ? AND ?
                               ORDER BY date DESC""", (date_from, date_to))
            rows = cur.fetchall()
        conn.close()

        for i, row in enumerate(rows):
            tid, date, total, payment, change, archived = row
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=str(tid), tags=(tag,),
                             values=(tid, date, f"₱{total:.2f}",
                                     f"₱{payment:.2f}", f"₱{change:.2f}", archived))

        count = len(rows)
        total_val = sum(r[2] for r in rows)
        view_month = self.view_month_var.get()
        period = f"{view_month} {self.view_year_var.get()}" if view_month != "All" else "All months"
        self.summary_var.set(
            f"Showing: {period}  |  Records: {count}  |  Total: \u20b1{total_val:.2f}"
        )

    def _archive_sales(self):
        month = MONTHS.index(self.month_var.get()) + 1
        year = int(self.year_var.get())
        date_from, date_to = _month_range(year, month)
        label = f"{self.month_var.get()} {year}"

        # Prevent archiving current month
        now = datetime.now()
        if year == now.year and month == now.month:
            messagebox.showwarning("Archive", "Cannot archive the current month.")
            return

        conn = connect_db()
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM transactions WHERE DATE(date) BETWEEN ? AND ?",
                        (date_from, date_to))
            count = cur.fetchone()[0]
        conn.close()

        if count == 0:
            messagebox.showinfo("Archive", f"No transactions found for {label}.")
            return

        if not messagebox.askyesno("Confirm Archive",
                                   f"Archive {count} transaction(s) for {label}?"):
            return

        conn = connect_db()
        with conn:
            cur = conn.cursor()
            cur.execute("""INSERT INTO transaction_archive (id, total, payment, change, date)
                           SELECT id, total, payment, change, date FROM transactions
                           WHERE DATE(date) BETWEEN ? AND ?""", (date_from, date_to))
            cur.execute("""INSERT INTO transaction_items_archive
                           (id, transaction_id, product_id, quantity, subtotal)
                           SELECT ti.id, ti.transaction_id, ti.product_id, ti.quantity, ti.subtotal
                           FROM transaction_items ti
                           JOIN transactions t ON ti.transaction_id = t.id
                           WHERE DATE(t.date) BETWEEN ? AND ?""", (date_from, date_to))
            cur.execute("""DELETE FROM transaction_items WHERE transaction_id IN
                           (SELECT id FROM transactions WHERE DATE(date) BETWEEN ? AND ?)""",
                        (date_from, date_to))
            cur.execute("DELETE FROM transactions WHERE DATE(date) BETWEEN ? AND ?",
                        (date_from, date_to))
        conn.close()

        messagebox.showinfo("Archive Successful",
                            f"{count} transaction(s) for {label} archived successfully.")
        self._load_archived()

    def _restore_by_month(self):
        month = MONTHS.index(self.restore_month_var.get()) + 1
        year = int(self.restore_year_var.get())
        date_from, date_to = _month_range(year, month)
        label = f"{self.restore_month_var.get()} {year}"

        conn = connect_db()
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?",
                        (date_from, date_to))
            count = cur.fetchone()[0]
        conn.close()

        if count == 0:
            messagebox.showinfo("Restore", f"No archived transactions found for {label}.")
            return

        if not messagebox.askyesno("Confirm Restore",
                                   f"Restore {count} transaction(s) for {label} back to active records?"):
            return

        conn = connect_db()
        with conn:
            cur = conn.cursor()
            cur.execute("""INSERT OR IGNORE INTO transactions (id, total, payment, change, date)
                           SELECT id, total, payment, change, date FROM transaction_archive
                           WHERE DATE(date) BETWEEN ? AND ?""", (date_from, date_to))
            cur.execute("""INSERT OR IGNORE INTO transaction_items
                           (id, transaction_id, product_id, quantity, subtotal)
                           SELECT id, transaction_id, product_id, quantity, subtotal
                           FROM transaction_items_archive
                           WHERE transaction_id IN (
                               SELECT id FROM transaction_archive
                               WHERE DATE(date) BETWEEN ? AND ?
                           )""", (date_from, date_to))
            cur.execute("""DELETE FROM transaction_items_archive
                           WHERE transaction_id IN (
                               SELECT id FROM transaction_archive
                               WHERE DATE(date) BETWEEN ? AND ?
                           )""", (date_from, date_to))
            cur.execute("DELETE FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?",
                        (date_from, date_to))
        conn.close()

        messagebox.showinfo("Restore Successful",
                            f"{count} transaction(s) for {label} restored successfully.")
        self._load_archived()

    def _delete_by_month(self):
        month = MONTHS.index(self.restore_month_var.get()) + 1
        year = int(self.restore_year_var.get())
        date_from, date_to = _month_range(year, month)
        label = f"{self.restore_month_var.get()} {year}"

        conn = connect_db()
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?",
                        (date_from, date_to))
            count = cur.fetchone()[0]
        conn.close()

        if count == 0:
            messagebox.showinfo("Delete", f"No archived transactions found for {label}.")
            return

        if not messagebox.askyesno("Confirm Delete",
                                   f"Permanently delete {count} archived transaction(s) for {label}?\n"
                                   "This cannot be undone."):
            return

        conn = connect_db()
        with conn:
            cur = conn.cursor()
            cur.execute("""DELETE FROM transaction_items_archive
                           WHERE transaction_id IN (
                               SELECT id FROM transaction_archive
                               WHERE DATE(date) BETWEEN ? AND ?
                           )""", (date_from, date_to))
            cur.execute("DELETE FROM transaction_archive WHERE DATE(date) BETWEEN ? AND ?",
                        (date_from, date_to))
        conn.close()

        messagebox.showinfo("Deleted", f"{count} record(s) for {label} permanently deleted.")
        self._load_archived()

    def _restore_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Restore", "Select at least one record to restore.")
            return

        if not messagebox.askyesno("Confirm Restore",
                                   f"Restore {len(selected)} transaction(s) back to active records?"):
            return

        conn = connect_db()
        with conn:
            cur = conn.cursor()
            for tid in selected:
                cur.execute("""INSERT OR IGNORE INTO transactions (id, total, payment, change, date)
                               SELECT id, total, payment, change, date
                               FROM transaction_archive WHERE id = ?""", (tid,))
                cur.execute("""INSERT OR IGNORE INTO transaction_items
                               (id, transaction_id, product_id, quantity, subtotal)
                               SELECT id, transaction_id, product_id, quantity, subtotal
                               FROM transaction_items_archive WHERE transaction_id = ?""", (tid,))
                cur.execute("DELETE FROM transaction_items_archive WHERE transaction_id = ?", (tid,))
                cur.execute("DELETE FROM transaction_archive WHERE id = ?", (tid,))
        conn.close()

        messagebox.showinfo("Restore Successful",
                            f"{len(selected)} transaction(s) restored successfully.")
        self._load_archived()

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Delete", "Select at least one record to delete.")
            return

        if not messagebox.askyesno("Confirm Delete",
                                   f"Permanently delete {len(selected)} archived transaction(s)?\n"
                                   "This cannot be undone."):
            return

        conn = connect_db()
        with conn:
            cur = conn.cursor()
            for tid in selected:
                cur.execute("DELETE FROM transaction_items_archive WHERE transaction_id = ?", (tid,))
                cur.execute("DELETE FROM transaction_archive WHERE id = ?", (tid,))
        conn.close()

        messagebox.showinfo("Deleted", f"{len(selected)} record(s) permanently deleted.")
        self._load_archived()


if __name__ == "__main__":
    root = tk.Tk()
    SalesArchive(root)
    root.mainloop()
