import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from dashboard_db import connect_db


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
        self.root.title("Sales Archive - Chizzling POS")
        self.root.geometry("1000x650")
        self.root.configure(bg="#FAF3E1")
        _ensure_archive_tables()
        self._build_ui()
        self._load_archived()

    def _build_ui(self):
        # Header
        tk.Label(self.root, text="SALES ARCHIVE", font=("Arial", 16, "bold"),
                 bg="#FF6600", fg="white").pack(fill="x", pady=0, ipady=12)

        # Controls
        ctrl = tk.Frame(self.root, bg="#FAF3E1")
        ctrl.pack(fill="x", padx=20, pady=12)

        tk.Label(ctrl, text="Archive month:",
                 font=("Arial", 11), bg="#FAF3E1").pack(side="left", padx=(0, 8))

        now = datetime.now()

        self.month_var = tk.StringVar(value=MONTHS[now.month - 2] if now.month > 1 else "December")
        month_cb = ttk.Combobox(ctrl, textvariable=self.month_var, width=12,
                                values=MONTHS, state="readonly")
        month_cb.pack(side="left")

        current_year = now.year
        self.year_var = tk.StringVar(value=str(current_year if now.month > 1 else current_year - 1))
        year_cb = ttk.Combobox(ctrl, textvariable=self.year_var, width=6,
                               values=[str(y) for y in range(current_year - 5, current_year + 1)],
                               state="readonly")
        year_cb.pack(side="left", padx=(4, 16))

        tk.Button(ctrl, text="Archive Month", command=self._archive_sales,
                  bg="#FF6600", fg="white", font=("Arial", 11, "bold"),
                  width=14, relief="raised").pack(side="left", padx=4)

        # Restore section
        tk.Label(ctrl, text="  |  Restore month:",
                 font=("Arial", 11), bg="#FAF3E1").pack(side="left", padx=(8, 8))

        self.restore_month_var = tk.StringVar(value=MONTHS[now.month - 2] if now.month > 1 else "December")
        ttk.Combobox(ctrl, textvariable=self.restore_month_var, width=12,
                     values=MONTHS, state="readonly").pack(side="left")

        self.restore_year_var = tk.StringVar(value=str(current_year if now.month > 1 else current_year - 1))
        ttk.Combobox(ctrl, textvariable=self.restore_year_var, width=6,
                     values=[str(y) for y in range(current_year - 5, current_year + 1)],
                     state="readonly").pack(side="left", padx=(4, 8))

        tk.Button(ctrl, text="Restore Month", command=self._restore_by_month,
                  bg="#28A745", fg="white", font=("Arial", 11, "bold"),
                  width=14, relief="raised").pack(side="left", padx=4)

        tk.Button(ctrl, text="Delete Month", command=self._delete_by_month,
                  bg="#DC3545", fg="white", font=("Arial", 11, "bold"),
                  width=13, relief="raised").pack(side="left", padx=4)

        # Summary label
        self.summary_var = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.summary_var,
                 font=("Arial", 10), bg="#FAF3E1", fg="#555").pack(anchor="w", padx=20)

        # View filter row
        view_row = tk.Frame(self.root, bg="#FAF3E1")
        view_row.pack(fill="x", padx=20, pady=(0, 6))

        tk.Label(view_row, text="View month:", font=("Arial", 11), bg="#FAF3E1").pack(side="left", padx=(0, 8))

        self.view_month_var = tk.StringVar(value="All")
        ttk.Combobox(view_row, textvariable=self.view_month_var, width=12,
                     values=["All"] + MONTHS, state="readonly").pack(side="left")

        self.view_year_var = tk.StringVar(value=str(current_year))
        ttk.Combobox(view_row, textvariable=self.view_year_var, width=6,
                     values=[str(y) for y in range(current_year - 5, current_year + 1)],
                     state="readonly").pack(side="left", padx=(4, 8))

        tk.Button(view_row, text="View", command=self._load_archived,
                  bg="#007BFF", fg="white", font=("Arial", 11, "bold"),
                  width=8, relief="raised").pack(side="left", padx=4)

        # Table
        table_frame = tk.Frame(self.root, bg="#FAF3E1")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        cols = ("ID", "Date", "Total", "Payment", "Change", "Archived On")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                 selectmode="extended")

        widths = [50, 160, 90, 90, 90, 160]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _load_archived(self):
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

        for row in rows:
            tid, date, total, payment, change, archived = row
            self.tree.insert("", "end", iid=str(tid),
                             values=(tid, date, f"\u20b1{total:.2f}",
                                     f"\u20b1{payment:.2f}", f"\u20b1{change:.2f}", archived))

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
