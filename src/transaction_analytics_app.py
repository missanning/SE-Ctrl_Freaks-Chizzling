import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime
import os

BG      = "#FFF8EE"
SIDEBAR = "#7a3b10"
ACCENT  = "#f5a623"
YELLOW  = "#ffd966"
FG_DARK = "#3b1f0a"
FG_LIGHT = "#fff3e0"
CONTENT = "#ffffff"
ROW_ALT = "#fff3e0"
FONT    = "Segoe UI"

CARD_PALETTE = [
    ("#7a3b10", "#fff3e0"),
    ("#f5a623", "#3b1f0a"),
    ("#ffd966", "#3b1f0a"),
]

def connect_db():
    db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
    return sqlite3.connect(db_path)


class TransactionAnalyticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transaction Analytics — Chizzling POS")
        self.root.state("zoomed")
        self.root.configure(bg=BG)
        self._build_ui()
        self.load_transactions()

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=SIDEBAR, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🧾  Transaction Analytics",
                 font=(FONT, 16, "bold"), bg=SIDEBAR, fg=YELLOW).pack(side="left", padx=24, pady=10)
        tk.Button(header, text="✕  Close", font=(FONT, 10, "bold"),
                  bg=SIDEBAR, fg="#ffaaaa", relief="flat", cursor="hand2",
                  activebackground="#8b0000", activeforeground="white",
                  command=self.root.destroy).pack(side="right", padx=16, pady=10)
        tk.Frame(self.root, bg=ACCENT, height=3).pack(fill="x")
        tk.Frame(self.root, bg=YELLOW, height=2).pack(fill="x")

        # ── Filter bar ────────────────────────────────────────────────────────
        filter_bar = tk.Frame(self.root, bg=CONTENT, pady=12)
        filter_bar.pack(fill="x", padx=24, pady=(16, 0))

        tk.Label(filter_bar, text="📅  Filter by Date:", font=(FONT, 12, "bold"),
                 bg=CONTENT, fg=FG_DARK).pack(side="left", padx=(0, 10))

        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_picker = DateEntry(filter_bar, textvariable=self.date_var,
                                     date_pattern="yyyy-mm-dd", width=13,
                                     background=SIDEBAR, foreground=FG_LIGHT,
                                     borderwidth=0, font=(FONT, 11))
        self.date_picker.pack(side="left", padx=(0, 10))
        self.date_picker.bind("<<DateEntrySelected>>", lambda e: self.load_transactions())

        tk.Button(filter_bar, text="Today", font=(FONT, 11, "bold"),
                  bg=ACCENT, fg=FG_DARK, relief="flat", padx=14, pady=4,
                  cursor="hand2", command=self._set_today).pack(side="left", padx=(0, 6))

        self.date_label = tk.Label(filter_bar, text="", font=(FONT, 11),
                                   bg=CONTENT, fg=FG_DARK)
        self.date_label.pack(side="left", padx=(16, 0))

        tk.Frame(self.root, bg=YELLOW, height=2).pack(fill="x", padx=24, pady=(12, 0))

        # ── Summary cards ─────────────────────────────────────────────────────
        self.summary_frame = tk.Frame(self.root, bg=BG)
        self.summary_frame.pack(fill="x", padx=24, pady=16)

        # ── Table section ─────────────────────────────────────────────────────
        table_header = tk.Frame(self.root, bg=CONTENT)
        table_header.pack(fill="x", padx=24)
        tk.Label(table_header, text="Transaction Records",
                 font=(FONT, 14, "bold"), bg=CONTENT, fg=SIDEBAR).pack(anchor="w", pady=(0, 6))
        tk.Frame(self.root, bg=ACCENT, height=2).pack(fill="x", padx=24, pady=(0, 8))

        tree_outer = tk.Frame(self.root, bg=CONTENT)
        tree_outer.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Themed.Treeview",
                         background=CONTENT, fieldbackground=CONTENT,
                         foreground=FG_DARK, font=(FONT, 11),
                         rowheight=32)
        style.configure("Themed.Treeview.Heading",
                         background=SIDEBAR, foreground=FG_LIGHT,
                         font=(FONT, 11, "bold"), relief="flat")
        style.map("Themed.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", FG_DARK)])

        cols = ("ID", "Date", "Time", "Total", "Payment", "Change")
        self.tree = ttk.Treeview(tree_outer, columns=cols, show="headings",
                                  style="Themed.Treeview", height=18)
        col_cfg = [("ID", 110, "center"), ("Date", 130, "center"),
                   ("Time", 120, "center"), ("Total", 160, "e"),
                   ("Payment", 160, "e"), ("Change", 160, "e")]
        for col, w, anchor in col_cfg:
            self.tree.heading(col, text=col.replace("ID", "Transaction ID"))
            self.tree.column(col, width=w, anchor=anchor)

        self.tree.tag_configure("odd",  background=CONTENT)
        self.tree.tag_configure("even", background=ROW_ALT)

        sb = ttk.Scrollbar(tree_outer, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # ── Bottom strip ──────────────────────────────────────────────────────
        tk.Frame(self.root, bg=ACCENT, height=3).pack(fill="x", side="bottom")
        tk.Frame(self.root, bg=SIDEBAR, height=8).pack(fill="x", side="bottom")

    def _make_card(self, parent, idx, label, value):
        bg, fg = CARD_PALETTE[idx]
        c = tk.Canvas(parent, bg=parent.cget("bg"), highlightthickness=0,
                      width=200, height=100)
        c.pack(side="left", padx=10, pady=4, fill="both", expand=True)
        def _draw(ev, c=c, bg=bg, fg=fg, label=label, value=value):
            c.delete("all")
            w, h = c.winfo_width(), c.winfo_height()
            if w < 10: return
            r = 16
            c.create_polygon(r,0, w-r,0, w,0, w,r, w,h-r, w,h,
                             w-r,h, r,h, 0,h, 0,h-r, 0,r, 0,0,
                             smooth=True, fill=bg, outline=bg)
            c.create_text(14, 14, text=label, font=(FONT, 11, "bold"), fill=fg, anchor="nw")
            c.create_text(14, 46, text=value, font=(FONT, 22, "bold"), fill=fg, anchor="nw")
        c.bind("<Configure>", _draw)
        c.after(50, lambda c=c: c.event_generate("<Configure>"))

    def _set_today(self):
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.load_transactions()

    def load_transactions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        selected_date = self.date_var.get()
        self.date_label.config(text=f"Showing: {selected_date}")

        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""SELECT id, date, total, payment, change
                              FROM transactions WHERE date LIKE ?
                              ORDER BY date DESC""", (selected_date + "%",))
            transactions = cursor.fetchall()

            total_sales  = sum(t[2] for t in transactions) if transactions else 0
            count        = len(transactions)
            avg          = total_sales / count if count else 0

            for w in self.summary_frame.winfo_children():
                w.destroy()
            self._make_card(self.summary_frame, 0, "🧾  TRANSACTIONS",      str(count))
            self._make_card(self.summary_frame, 1, "📈  AVG TRANSACTION",   f"₱{avg:,.2f}")
            self._make_card(self.summary_frame, 2, "💰  TOTAL SALES",       f"₱{total_sales:,.2f}")

            for i, (tid, dt, total, payment, change) in enumerate(transactions):
                try:
                    d = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                    date_str, time_str = d.strftime("%Y-%m-%d"), d.strftime("%H:%M:%S")
                except Exception:
                    parts = dt.split() if dt else ["", ""]
                    date_str = parts[0]
                    time_str = parts[1] if len(parts) > 1 else "00:00:00"

                tag = "even" if i % 2 == 0 else "odd"
                self.tree.insert("", "end", tags=(tag,), values=(
                    tid, date_str, time_str,
                    f"₱{total:,.2f}", f"₱{payment:,.2f}", f"₱{change:,.2f}"
                ))

            if not transactions:
                self.tree.insert("", "end", values=(
                    "—", "No transactions found", "—", "—", "—", "—"))

        except Exception as e:
            print(f"Error loading transactions: {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    TransactionAnalyticsApp(root)
    root.mainloop()
