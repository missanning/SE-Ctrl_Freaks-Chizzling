import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
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

        tk.Label(ctrl, text="Archive transactions older than:",
                 font=("Arial", 11), bg="#FAF3E1").pack(side="left", padx=(0, 8))

        self.days_var = tk.StringVar(value="30")
        days_cb = ttk.Combobox(ctrl, textvariable=self.days_var, width=8,
                               values=["30", "60", "90", "180", "365"], state="readonly")
        days_cb.pack(side="left")

        tk.Label(ctrl, text="days", font=("Arial", 11), bg="#FAF3E1").pack(side="left", padx=(4, 16))

        tk.Button(ctrl, text="Archive Now", command=self._archive_sales,
                  bg="#FF6600", fg="white", font=("Arial", 11, "bold"),
                  width=14, relief="raised").pack(side="left", padx=4)

        tk.Button(ctrl, text="Restore Selected", command=self._restore_selected,
                  bg="#28A745", fg="white", font=("Arial", 11, "bold"),
                  width=16, relief="raised").pack(side="left", padx=4)

        tk.Button(ctrl, text="Delete Selected", command=self._delete_selected,
                  bg="#DC3545", fg="white", font=("Arial", 11, "bold"),
                  width=14, relief="raised").pack(side="left", padx=4)

        # Summary label
        self.summary_var = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.summary_var,
                 font=("Arial", 10), bg="#FAF3E1", fg="#555").pack(anchor="w", padx=20)

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
            cur.execute("""SELECT id, date, total, payment, change, archived_date
                           FROM transaction_archive ORDER BY archived_date DESC""")
            rows = cur.fetchall()
        conn.close()

        for row in rows:
            tid, date, total, payment, change, archived = row
            self.tree.insert("", "end", iid=str(tid),
                             values=(tid, date, f"₱{total:.2f}",
                                     f"₱{payment:.2f}", f"₱{change:.2f}", archived))

        count = len(rows)
        total_val = sum(r[2] for r in rows)
        self.summary_var.set(
            f"Archived records: {count}  |  Total archived sales: ₱{total_val:.2f}"
        )

    def _archive_sales(self):
        days = int(self.days_var.get())
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        conn = connect_db()
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM transactions WHERE DATE(date) < ?", (cutoff,))
            count = cur.fetchone()[0]

        conn.close()

        if count == 0:
            messagebox.showinfo("Archive", f"No transactions older than {days} days found.")
            return

        if not messagebox.askyesno("Confirm Archive",
                                   f"Archive {count} transaction(s) older than {days} days?\n"
                                   f"(Cutoff: {cutoff})"):
            return

        conn = connect_db()
        with conn:
            cur = conn.cursor()

            # Move transactions
            cur.execute("""INSERT INTO transaction_archive (id, total, payment, change, date)
                           SELECT id, total, payment, change, date
                           FROM transactions WHERE DATE(date) < ?""", (cutoff,))

            # Move transaction items
            cur.execute("""INSERT INTO transaction_items_archive
                           (id, transaction_id, product_id, quantity, subtotal)
                           SELECT ti.id, ti.transaction_id, ti.product_id, ti.quantity, ti.subtotal
                           FROM transaction_items ti
                           JOIN transactions t ON ti.transaction_id = t.id
                           WHERE DATE(t.date) < ?""", (cutoff,))

            # Delete from main tables
            cur.execute("""DELETE FROM transaction_items WHERE transaction_id IN
                           (SELECT id FROM transactions WHERE DATE(date) < ?)""", (cutoff,))
            cur.execute("DELETE FROM transactions WHERE DATE(date) < ?", (cutoff,))

        conn.close()
        messagebox.showinfo("Archive Successful", f"{count} transaction(s) archived successfully.")
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
