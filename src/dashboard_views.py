import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from dashboard_db import connect_db, get_date_range
import dashboard_charts as charts


class DashboardViews:
    """Mixin: all view/UI methods for Dashboard."""

    # ── Shared helpers ────────────────────────────────────────────────────────

    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def _make_card(self, parent, color, label, value, value_font_size=24, fg="white"):
        card = tk.Frame(parent, bg=color, bd=3, relief="raised")
        card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        tk.Label(card, text=label, font=("Arial", 12, "bold"), bg=color, fg=fg).pack(pady=(15, 5))
        tk.Label(card, text=value, font=("Arial", value_font_size, "bold"), bg=color, fg=fg).pack(pady=(0, 15))
        return card

    def _make_table_row(self, parent, row, cols, widths, bg, bold=False):
        for col, (text, width) in enumerate(zip(cols, widths)):
            font = ("Arial", 10, "bold") if bold else ("Arial", 10)
            tk.Label(parent, text=text, font=font, bg=bg,
                     width=width, relief="solid", bd=1).grid(row=row, column=col, sticky="ew")

    # ── Daily Sales ───────────────────────────────────────────────────────────

    def show_daily_sales(self):
        self.clear_content()
        today = datetime.now().strftime("%Y-%m-%d")

        conn = connect_db()
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(total) FROM transactions WHERE date LIKE ?", (today + '%',))
            r = cursor.fetchone()
        conn.close()

        count = r[0] or 0
        total = r[1] or 0.0
        avg = total / count if count else 0

        tk.Label(self.content_frame, text="📊 DAILY SALES OVERVIEW",
                 font=("Arial", 16, "bold"), bg="#FFFFFF", fg="#FF6600").pack(pady=15)

        cards = tk.Frame(self.content_frame, bg="#FFFFFF")
        cards.pack(pady=20, padx=20, fill="x")
        self._make_card(cards, "#28A745", "💰 TODAY'S TOTAL SALES", f"₱{total:.2f}")
        self._make_card(cards, "#007BFF", "🧾 TRANSACTIONS", str(count))
        self._make_card(cards, "#FFC107", "📈 AVG TRANSACTION", f"₱{avg:.2f}", value_font_size=20)

        tk.Label(self.content_frame, text=f"📅 Date: {today}",
                 font=("Arial", 14, "bold"), bg="#FFFFFF", fg="#666666").pack(pady=10)

        perf = tk.Frame(self.content_frame, bg="#F8F9FA", bd=1, relief="solid")
        perf.pack(pady=15, padx=20, fill="x")
        tk.Label(perf, text="📊 Quick Performance Summary",
                 font=("Arial", 12, "bold"), bg="#F8F9FA").pack(pady=(10, 5))
        msg = f"Today you processed {count} transactions with total sales of ₱{total:.2f}"
        msg += f"\nAverage transaction value: ₱{avg:.2f}" if count else "\nNo transactions recorded today."
        tk.Label(perf, text=msg, font=("Arial", 11), bg="#F8F9FA", justify="center").pack(pady=(0, 10))

    # ── Weekly Sales ──────────────────────────────────────────────────────────

    def show_weekly_sales(self):
        self.clear_content()
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        date_from = monday.strftime("%Y-%m-%d")
        date_to = sunday.strftime("%Y-%m-%d")

        conn = connect_db()
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(total) FROM transactions WHERE DATE(date) BETWEEN ? AND ?",
                           (date_from, date_to))
            r = cursor.fetchone()
        count = r[0] or 0
        total = r[1] or 0.0
        days_elapsed = (today - monday).days + 1
        avg_daily = total / days_elapsed if days_elapsed else 0

        tk.Label(self.content_frame, text="📈 WEEKLY SALES OVERVIEW",
                 font=("Arial", 16, "bold"), bg="#FFFFFF", fg="#007BFF").pack(pady=15)

        cards = tk.Frame(self.content_frame, bg="#FFFFFF")
        cards.pack(pady=20, padx=20, fill="x")
        self._make_card(cards, "#007BFF", "💰 TOTAL WEEKLY SALES", f"₱{total:.2f}")
        self._make_card(cards, "#28A745", "📅 DAILY AVERAGE", f"₱{avg_daily:.2f}", value_font_size=20)
        self._make_card(cards, "#FFC107", "🧾 TOTAL TRANSACTIONS", str(count))

        tk.Label(self.content_frame, text=f"📅 Week Period: {date_from} to {date_to}",
                 font=("Arial", 14, "bold"), bg="#FFFFFF", fg="#666666").pack(pady=10)

        perf = tk.Frame(self.content_frame, bg="#F8F9FA", bd=1, relief="solid")
        perf.pack(pady=15, padx=20, fill="x")
        tk.Label(perf, text="📊 Weekly Performance Summary",
                 font=("Arial", 12, "bold"), bg="#F8F9FA").pack(pady=(10, 5))
        msg = (f"This week you processed {count} transactions with total sales of ₱{total:.2f}\n"
               f"Daily average: ₱{avg_daily:.2f} over {days_elapsed} days")
        if count:
            msg += f"\nAverage transaction value: ₱{total/count:.2f}"
        tk.Label(perf, text=msg, font=("Arial", 11), bg="#F8F9FA", justify="center").pack(pady=(0, 10))

        # Daily breakdown table
        conn2 = connect_db()
        with conn2:
            cursor2 = conn2.cursor()
            cursor2.execute("""SELECT DATE(date), COUNT(*), SUM(total) FROM transactions
                              WHERE DATE(date) BETWEEN ? AND ?
                              GROUP BY DATE(date) ORDER BY DATE(date) DESC""", (date_from, date_to))
            daily_data = cursor2.fetchall()
        conn2.close()

        breakdown = tk.Frame(self.content_frame, bg="#FFFFFF")
        breakdown.pack(pady=15, padx=20, fill="both", expand=True)
        tk.Label(breakdown, text="📈 Daily Breakdown", font=("Arial", 12, "bold"), bg="#FFFFFF").pack(pady=(0, 10))

        if daily_data:
            tbl = tk.Frame(breakdown, bg="#FFFFFF")
            tbl.pack()
            self._make_table_row(tbl, 0, ["Date", "Transactions", "Sales"], [15, 15, 15],
                                 "#E9ECEF", bold=True)
            for i, (date, trans, sales) in enumerate(daily_data, 1):
                bg = "#F8F9FA" if i % 2 == 0 else "#FFFFFF"
                self._make_table_row(tbl, i, [date, str(trans), f"₱{sales:.2f}"], [15, 15, 15], bg)
        else:
            tk.Label(breakdown, text="No sales data available for this week",
                     font=("Arial", 11), bg="#FFFFFF", fg="#666666").pack(pady=20)

    # ── Top Products ──────────────────────────────────────────────────────────

    def show_top_products(self):
        self.clear_content()
        tk.Label(self.content_frame, text="TOP SELLING PRODUCTS",
                 font=("Arial", 14, "bold"), bg="#FFFFFF").pack(pady=10)

        period_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        period_frame.pack(pady=10)
        tk.Label(period_frame, text="View:", font=("Arial", 11), bg="#FFFFFF").pack(side="left", padx=5)

        self.period_var = tk.StringVar(value="daily")
        for text, val in [("Daily", "daily"), ("Weekly", "weekly")]:
            tk.Radiobutton(period_frame, text=text, variable=self.period_var, value=val,
                           bg="#FFFFFF", command=lambda: self.update_top_products(self.period_var.get())
                           ).pack(side="left", padx=5)

        self.graph_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.update_top_products("daily")

    def update_top_products(self, period):
        for w in self.graph_frame.winfo_children():
            w.destroy()

        date_from, date_to, title = get_date_range(period)
        conn = connect_db()
        with conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT p.name, SUM(ti.quantity), SUM(ti.subtotal)
                              FROM transaction_items ti
                              JOIN products p ON ti.product_id=p.id
                              JOIN transactions t ON ti.transaction_id=t.id
                              WHERE DATE(t.date) BETWEEN ? AND ?
                              GROUP BY p.id, p.name ORDER BY 2 DESC LIMIT 5""", (date_from, date_to))
            results = cursor.fetchall()
        conn.close()

        if not results:
            tk.Label(self.graph_frame, text="No sales data available for this period",
                     font=("Arial", 12), bg="#FFFFFF").pack(pady=50)
            return

        products = [r[0] for r in results]
        quantities = [r[1] for r in results]
        sales = [r[2] for r in results]

        fig = charts.build_top_products_figure(products, quantities, sales, title,
                                               self.root.winfo_screenwidth())

        btn_frame = tk.Frame(self.graph_frame, bg="#FFFFFF")
        btn_frame.pack(pady=20, fill="x")
        tk.Button(btn_frame, text="View Interactive Chart",
                  command=lambda: charts.open_top_products_chart(fig),
                  bg="#FF6600", fg="white", font=("Arial", 14, "bold"),
                  width=30, height=2, relief="raised", bd=3).pack()

        self._create_summary_table(products, quantities, sales)

        tk.Button(self.graph_frame, text="📈 View Sales Progression Chart",
                  command=lambda: charts.open_sales_time_series(period, self.root.winfo_screenwidth()),
                  bg="#28A745", fg="white", font=("Arial", 12, "bold"),
                  width=30, height=2, relief="raised", bd=2).pack(pady=10)

    def _create_summary_table(self, products, quantities, sales):
        container = tk.Frame(self.graph_frame, bg="#FFFFFF")
        container.pack(pady=20, fill="x")
        tbl_outer = tk.Frame(container, bg="#F8F9FA", bd=2, relief="raised")
        tbl_outer.pack(expand=True)
        tk.Label(tbl_outer, text="Top Products Summary", font=("Arial", 14, "bold"),
                 bg="#F8F9FA").pack(pady=15)
        tbl = tk.Frame(tbl_outer, bg="#F8F9FA")
        tbl.pack(fill="x", padx=20)
        self._make_table_row(tbl, 0, ["Product", "Quantity", "Revenue"], [30, 12, 18],
                             "#E9ECEF", bold=True)
        for i, (p, q, s) in enumerate(zip(products, quantities, sales), 1):
            bg = "#FFFFFF" if i % 2 == 0 else "#F8F9FA"
            name = p if len(p) <= 35 else p[:32] + "..."
            tk.Label(tbl, text=name, font=("Arial", 11), bg=bg,
                     width=30, relief="solid", bd=1, anchor="w").grid(row=i, column=0, sticky="ew")
            tk.Label(tbl, text=str(int(q)), font=("Arial", 11), bg=bg,
                     width=12, relief="solid", bd=1).grid(row=i, column=1, sticky="ew")
            tk.Label(tbl, text=f"₱{s:.2f}", font=("Arial", 11), bg=bg,
                     width=18, relief="solid", bd=1).grid(row=i, column=2, sticky="ew")

    # ── Revenue Analysis ──────────────────────────────────────────────────────

    def show_revenue_analysis(self):
        self.clear_content()
        tk.Label(self.content_frame, text="💰 REVENUE ANALYSIS",
                 font=("Arial", 16, "bold"), bg="#FFFFFF", fg="#17A2B8").pack(pady=15)

        period_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        period_frame.pack(pady=10)
        tk.Label(period_frame, text="Analysis Period:", font=("Arial", 11, "bold"),
                 bg="#FFFFFF").pack(side="left", padx=5)

        self.revenue_period_var = tk.StringVar(value="daily")
        for text, val in [("Daily", "daily"), ("Weekly", "weekly"), ("Monthly", "monthly")]:
            tk.Radiobutton(period_frame, text=text, variable=self.revenue_period_var, value=val,
                           bg="#FFFFFF",
                           command=lambda: self.update_revenue_analysis(self.revenue_period_var.get())
                           ).pack(side="left", padx=5)

        self.revenue_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        self.revenue_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.update_revenue_analysis("daily")

    def update_revenue_analysis(self, period):
        for w in self.revenue_frame.winfo_children():
            w.destroy()

        date_from, date_to, title = get_date_range(period)
        conn = connect_db()
        with conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT p.name, p.price, SUM(ti.quantity), SUM(ti.subtotal),
                                     AVG(p.price), (SUM(ti.subtotal)/SUM(ti.quantity))
                              FROM transaction_items ti
                              JOIN products p ON ti.product_id=p.id
                              JOIN transactions t ON ti.transaction_id=t.id
                              WHERE DATE(t.date) BETWEEN ? AND ?
                              GROUP BY p.id, p.name, p.price HAVING SUM(ti.quantity)>0
                              ORDER BY 4 DESC""", (date_from, date_to))
            results = cursor.fetchall()
        conn.close()

        if not results:
            tk.Label(self.revenue_frame, text="No sales data available for this period",
                     font=("Arial", 14), bg="#FFFFFF", fg="#666666").pack(pady=50)
            return

        self._create_revenue_summary(results)
        self._create_revenue_table(results)

        tk.Button(self.revenue_frame, text="📊 View Interactive Revenue Chart",
                  command=lambda: charts.open_revenue_chart(results, title, self.root.winfo_screenwidth()),
                  bg="#17A2B8", fg="white", font=("Arial", 14, "bold"),
                  width=40, height=2, relief="raised", bd=3).pack(pady=20)

        tk.Button(self.revenue_frame, text="📈 View Revenue Progression Chart",
                  command=lambda: charts.open_revenue_time_series(period, self.root.winfo_screenwidth()),
                  bg="#28A745", fg="white", font=("Arial", 12, "bold"),
                  width=30, height=2, relief="raised", bd=2).pack(pady=10)

    def _create_revenue_summary(self, results):
        total_rev = sum(r[3] for r in results)
        total_qty = sum(r[2] for r in results)
        avg_price = total_rev / total_qty if total_qty else 0

        cards = tk.Frame(self.revenue_frame, bg="#FFFFFF")
        cards.pack(pady=20, padx=20, fill="x")
        self._make_card(cards, "#28A745", "💰 TOTAL REVENUE", f"₱{total_rev:.2f}")
        self._make_card(cards, "#007BFF", "📋 ITEMS SOLD", str(int(total_qty)))
        self._make_card(cards, "#17A2B8", "📊 AVG PRICE", f"₱{avg_price:.2f}", value_font_size=20)

        top = results[0]
        top_card = tk.Frame(cards, bg="#FFC107", bd=3, relief="raised")
        top_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        tk.Label(top_card, text="🏆 TOP PRODUCT", font=("Arial", 12, "bold"),
                 bg="#FFC107", fg="black").pack(pady=(15, 5))
        name = top[0][:15] + "..." if len(top[0]) > 15 else top[0]
        tk.Label(top_card, text=name, font=("Arial", 12, "bold"), bg="#FFC107", fg="black").pack()
        tk.Label(top_card, text=f"₱{top[3]:.0f}", font=("Arial", 16, "bold"),
                 bg="#FFC107", fg="black").pack(pady=(0, 15))

    def _create_revenue_table(self, results):
        container = tk.Frame(self.revenue_frame, bg="#FFFFFF")
        container.pack(pady=20, fill="both", expand=True)
        tk.Label(container, text="📋 Detailed Revenue Report",
                 font=("Arial", 14, "bold"), bg="#FFFFFF").pack(pady=(0, 15))

        canvas = tk.Canvas(container, bg="#FFFFFF", height=300)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#FFFFFF")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        headers = ["Product", "Unit Price", "Qty Sold", "Total Revenue", "Avg Revenue/Unit", "Revenue %"]
        hdr = tk.Frame(scroll_frame, bg="#FFFFFF")
        hdr.pack(fill="x", padx=10)
        for i, h in enumerate(headers):
            tk.Label(hdr, text=h, font=("Arial", 10, "bold"), bg="#E9ECEF",
                     width=25 if i == 0 else 15, relief="solid", bd=1).grid(row=0, column=i, sticky="ew")

        total_rev = sum(r[3] for r in results)
        for idx, data in enumerate(results[:20], 1):
            bg = "#F8F9FA" if idx % 2 == 0 else "#FFFFFF"
            pct = data[3] / total_rev * 100 if total_rev else 0
            pct_color = "#28A745" if pct > 10 else "#FFC107" if pct > 5 else "#6C757D"
            name = data[0][:30] + "..." if len(data[0]) > 30 else data[0]
            row_vals = [name, f"₱{data[1]:.0f}", str(int(data[2])),
                        f"₱{data[3]:.0f}", f"₱{data[5]:.0f}", f"{pct:.1f}%"]
            for col, (val, w) in enumerate(zip(row_vals, [25, 15, 15, 15, 15, 15])):
                kw = dict(font=("Arial", 9), bg=bg, width=w, relief="solid", bd=1)
                if col == 3:
                    kw.update(font=("Arial", 9, "bold"), fg="#28A745")
                elif col == 5:
                    kw.update(font=("Arial", 9, "bold"), fg=pct_color)
                tk.Label(hdr, text=val, **kw).grid(row=idx, column=col, sticky="ew")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
