import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from dashboard_db import connect_db, get_date_range
import dashboard_charts as charts

BG      = "#FFF8EE"
ACCENT  = "#f5a623"
YELLOW  = "#ffd966"
SIDEBAR = "#7a3b10"
FG_DARK = "#3b1f0a"
FG_LIGHT = "#fff3e0"
CONTENT = "#ffffff"
ROW_ALT = "#fff3e0"
HDR_BG  = "#7a3b10"
FONT    = "Segoe UI"

CARD_PALETTE = [
    ("#7a3b10", "#fff3e0"),
    ("#f5a623", "#3b1f0a"),
    ("#ffd966", "#3b1f0a"),
    ("#5c2e00", "#fff3e0"),
]


class DashboardViews:

    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def _section_title(self, parent, text):
        tk.Label(parent, text=text, font=(FONT, 18, "bold"),
                 bg=CONTENT, fg=SIDEBAR).pack(anchor="w", pady=(0, 4))
        tk.Frame(parent, bg=ACCENT, height=3).pack(fill="x", pady=(0, 16))

    def _make_card(self, parent, idx, label, value, value_font_size=26):
        bg, fg = CARD_PALETTE[idx % len(CARD_PALETTE)]
        # Canvas-based rounded card
        canvas = tk.Canvas(parent, bg=parent.cget("bg"), highlightthickness=0,
                           width=200, height=110)
        canvas.pack(side="left", padx=8, pady=8, fill="both", expand=True)

        def _draw(c=canvas, color=bg):
            c.delete("all")
            w, h = c.winfo_width(), c.winfo_height()
            if w < 10 or h < 10:
                return
            r = 18
            c.create_polygon(
                r, 0, w-r, 0, w, 0, w, r, w, h-r, w, h, w-r, h,
                r, h, 0, h, 0, h-r, 0, r, 0, 0,
                smooth=True, fill=color, outline=color
            )
            c.create_text(14, 14, text=label, font=(FONT, 12, "bold"),
                          fill=fg, anchor="nw")
            c.create_text(14, 48, text=value, font=(FONT, value_font_size, "bold"),
                          fill=fg, anchor="nw")

        canvas.bind("<Configure>", lambda e: _draw())
        canvas.after(50, _draw)

    def _make_table(self, parent, headers, rows):
        tbl = tk.Frame(parent, bg=CONTENT)
        tbl.pack(fill="x", pady=(8, 0))
        widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) + 4
                  for i, h in enumerate(headers)]
        # header row
        for c, (h, w) in enumerate(zip(headers, widths)):
            tk.Label(tbl, text=h, font=(FONT, 12, "bold"), bg=HDR_BG,
                     fg=FG_LIGHT, width=w, relief="flat", padx=8, pady=8,
                     anchor="w").grid(row=0, column=c, sticky="ew", padx=1, pady=1)
        # data rows
        for r, row in enumerate(rows, 1):
            bg = ROW_ALT if r % 2 == 0 else CONTENT
            for c, (val, w) in enumerate(zip(row, widths)):
                tk.Label(tbl, text=val, font=(FONT, 12), bg=bg,
                         fg=FG_DARK, width=w, relief="flat", padx=8, pady=6,
                         anchor="w").grid(row=r, column=c, sticky="ew", padx=1, pady=1)

    def _themed_button(self, parent, text, cmd, primary=True):
        bg = SIDEBAR if primary else ACCENT
        fg = FG_LIGHT if primary else FG_DARK
        btn = tk.Button(parent, text=text, command=cmd, font=(FONT, 13, "bold"),
                        bg=bg, fg=fg, relief="flat", padx=24, pady=10,
                        activebackground=ACCENT, activeforeground=FG_DARK,
                        cursor="hand2")
        btn.pack(pady=6)
        return btn

    def _period_selector(self, parent, var, options, callback):
        frame = tk.Frame(parent, bg=CONTENT)
        frame.pack(anchor="w", pady=(0, 12))
        tk.Label(frame, text="Period:", font=(FONT, 12, "bold"),
                 bg=CONTENT, fg=FG_DARK).pack(side="left", padx=(0, 8))
        for text, val in options:
            rb = tk.Radiobutton(frame, text=text, variable=var, value=val,
                                bg=CONTENT, fg=FG_DARK, selectcolor=YELLOW,
                                activebackground=CONTENT, font=(FONT, 12),
                                command=callback)
            rb.pack(side="left", padx=6)

    def _get_prev_range(self, period):
        """Return (date_from, date_to) for the period immediately before the current one."""
        today = datetime.now()
        if period == "daily":
            prev = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            return prev, prev
        elif period == "weekly":
            monday = today - timedelta(days=today.weekday())
            prev_mon = monday - timedelta(weeks=1)
            prev_sun = prev_mon + timedelta(days=6)
            return prev_mon.strftime("%Y-%m-%d"), prev_sun.strftime("%Y-%m-%d")
        else:
            first = today.replace(day=1)
            prev_last = first - timedelta(days=1)
            prev_first = prev_last.replace(day=1)
            return prev_first.strftime("%Y-%m-%d"), prev_last.strftime("%Y-%m-%d")

    def _trend_label(self, parent, bg, current, previous):
        """Pack a small trend indicator label onto parent."""
        if previous and previous > 0:
            pct = (current - previous) / previous * 100
            up  = pct >= 0
            txt = f"{'↑' if up else '↓'} {abs(pct):.1f}%"
            fg  = "#2d6a2d" if up else "#8b0000"
            tk.Label(parent, text=txt, font=(FONT, 11, "bold"),
                     bg=bg, fg=fg).pack(side="left", padx=(16, 0))

    def _trend_text(self, current, previous):
        """Return trend string for canvas drawing."""
        if previous and previous > 0:
            pct = (current - previous) / previous * 100
            return (f"{'↑' if pct >= 0 else '↓'} {abs(pct):.1f}%",
                    "#2d6a2d" if pct >= 0 else "#ff6666")
        return ("", None)

    def _perf_box(self, parent, msg):
        box = tk.Frame(parent, bg=YELLOW, padx=16, pady=14)
        box.pack(fill="x", pady=(12, 0))
        tk.Label(box, text=msg, font=(FONT, 13), bg=YELLOW,
                 fg=FG_DARK, justify="left").pack(anchor="w")

    # ── Daily Sales ───────────────────────────────────────────────────────────

    def show_daily_sales(self):
        self.clear_content()
        if hasattr(self, 'header_label'):
            self.header_label.config(text="📊  Daily Sales")
        today = datetime.now().strftime("%Y-%m-%d")

        conn = connect_db()
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(total) FROM transactions WHERE date LIKE ?", (today + '%',))
            r = cursor.fetchone()
        conn.close()

        count = r[0] or 0
        total = r[1] or 0.0
        avg   = total / count if count else 0

        self._section_title(self.content_frame, "Daily Sales Overview")

        cards = tk.Frame(self.content_frame, bg=CONTENT)
        cards.pack(fill="x", pady=(0, 16))
        self._make_card(cards, 0, "💰  TODAY'S TOTAL SALES", f"₱{total:,.2f}")
        self._make_card(cards, 1, "🧾  TRANSACTIONS",        str(count))
        self._make_card(cards, 2, "📈  AVG TRANSACTION",     f"₱{avg:,.2f}", 18)

        tk.Label(self.content_frame, text=f"📅  {today}",
                 font=(FONT, 13), bg=CONTENT, fg=FG_DARK).pack(anchor="w", pady=(0, 8))

        msg = f"Processed {count} transaction(s) — Total: ₱{total:,.2f}"
        if count:
            msg += f"   |   Avg: ₱{avg:,.2f}"
        else:
            msg += "\nNo transactions recorded today."
        self._perf_box(self.content_frame, msg)

    # ── Weekly Sales ──────────────────────────────────────────────────────────

    def show_weekly_sales(self):
        self.clear_content()
        if hasattr(self, 'header_label'):
            self.header_label.config(text="📈  Weekly Sales")
        today  = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        date_from = monday.strftime("%Y-%m-%d")
        date_to   = sunday.strftime("%Y-%m-%d")

        conn = connect_db()
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(total) FROM transactions WHERE DATE(date) BETWEEN ? AND ?",
                           (date_from, date_to))
            r = cursor.fetchone()
            cursor.execute("""SELECT DATE(date), COUNT(*), SUM(total) FROM transactions
                              WHERE DATE(date) BETWEEN ? AND ?
                              GROUP BY DATE(date) ORDER BY DATE(date) DESC""", (date_from, date_to))
            daily_data = cursor.fetchall()
        conn.close()

        count        = r[0] or 0
        total        = r[1] or 0.0
        days_elapsed = (today - monday).days + 1
        avg_daily    = total / days_elapsed if days_elapsed else 0

        self._section_title(self.content_frame, "Weekly Sales Overview")

        cards = tk.Frame(self.content_frame, bg=CONTENT)
        cards.pack(fill="x", pady=(0, 16))
        self._make_card(cards, 0, "💰  TOTAL WEEKLY SALES", f"₱{total:,.2f}")
        self._make_card(cards, 1, "📅  DAILY AVERAGE",      f"₱{avg_daily:,.2f}", 18)
        self._make_card(cards, 2, "🧾  TOTAL TRANSACTIONS", str(count))

        tk.Label(self.content_frame, text=f"📅  {date_from}  →  {date_to}",
                 font=(FONT, 13), bg=CONTENT, fg=FG_DARK).pack(anchor="w", pady=(0, 8))

        msg = f"Week total: ₱{total:,.2f} over {days_elapsed} day(s)   |   {count} transaction(s)"
        if count:
            msg += f"   |   Avg per transaction: ₱{total/count:,.2f}"
        self._perf_box(self.content_frame, msg)

        tk.Label(self.content_frame, text="Daily Breakdown",
                 font=(FONT, 14, "bold"), bg=CONTENT, fg=SIDEBAR).pack(anchor="w", pady=(16, 4))

        if daily_data:
            rows = [(d, str(t), f"₱{s:,.2f}") for d, t, s in daily_data]
            self._make_table(self.content_frame, ["Date", "Transactions", "Sales"], rows)
        else:
            tk.Label(self.content_frame, text="No sales data available for this week.",
                     font=(FONT, 13), bg=CONTENT, fg=FG_DARK).pack(anchor="w", pady=12)

    # ── Top Products ──────────────────────────────────────────────────────────

    def show_top_products(self):
        self.clear_content()
        if hasattr(self, 'header_label'):
            self.header_label.config(text="🏆  Top Products")
        self._section_title(self.content_frame, "Top Selling Products")

        self.period_var = tk.StringVar(value="daily")
        self._period_selector(self.content_frame, self.period_var,
                              [("Daily", "daily"), ("Weekly", "weekly")],
                              lambda: self.update_top_products(self.period_var.get()))

        self.graph_frame = tk.Frame(self.content_frame, bg=CONTENT)
        self.graph_frame.pack(fill="both", expand=True)
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
            tk.Label(self.graph_frame, text="No sales data available for this period.",
                     font=(FONT, 13), bg=CONTENT, fg=FG_DARK).pack(pady=40)
            return

        products   = [r[0] for r in results]
        quantities = [r[1] for r in results]
        sales      = [r[2] for r in results]
        max_qty    = max(quantities) if quantities else 1
        max_rev    = max(sales) if sales else 1
        total_qty  = sum(quantities)
        total_rev  = sum(sales)

        # fetch previous period totals for trend
        prev_from, prev_to = self._get_prev_range(period)
        conn2 = connect_db()
        with conn2:
            cur2 = conn2.cursor()
            cur2.execute("""SELECT p.name, SUM(ti.quantity), SUM(ti.subtotal)
                            FROM transaction_items ti
                            JOIN products p ON ti.product_id=p.id
                            JOIN transactions t ON ti.transaction_id=t.id
                            WHERE DATE(t.date) BETWEEN ? AND ?
                            GROUP BY p.id, p.name ORDER BY 2 DESC LIMIT 5""", (prev_from, prev_to))
            prev_results = cur2.fetchall()
        conn2.close()
        prev_map     = {r[0]: (r[1], r[2]) for r in prev_results}
        prev_tot_qty = sum(r[1] for r in prev_results)
        prev_tot_rev = sum(r[2] for r in prev_results)

        # ── Summary strip ────────────────────────────────────────────────────
        strip = tk.Frame(self.graph_frame, bg=YELLOW, padx=16, pady=12)
        strip.pack(fill="x", pady=(0, 16))
        tk.Label(strip, text=f"📦  Total Items Sold: {int(total_qty):,}",
                 font=(FONT, 13, "bold"), bg=YELLOW, fg=FG_DARK).pack(side="left")
        self._trend_label(strip, YELLOW, total_qty, prev_tot_qty)
        tk.Label(strip, text=f"   💰  Total Revenue: ₱{total_rev:,.2f}",
                 font=(FONT, 13, "bold"), bg=YELLOW, fg=FG_DARK).pack(side="left", padx=(24, 0))
        self._trend_label(strip, YELLOW, total_rev, prev_tot_rev)
        period_lbl = "vs yesterday" if period == "daily" else "vs last week"
        tk.Label(strip, text=f"  ({period_lbl})", font=(FONT, 10),
                 bg=YELLOW, fg=FG_DARK).pack(side="left")

        # ── Podium cards (top 3) ─────────────────────────────────────────────
        medals  = ["🥇", "🥈", "🥉"]
        p_colors = ["#f5a623", "#7a3b10", "#5c2e00"]
        p_fgs    = ["#3b1f0a", "#fff3e0", "#fff3e0"]
        podium = tk.Frame(self.graph_frame, bg=CONTENT)
        podium.pack(fill="x", pady=(0, 16))
        for i, (name, qty, rev) in enumerate(zip(products[:3], quantities[:3], sales[:3])):
            c = tk.Canvas(podium, bg=CONTENT, highlightthickness=0, width=220, height=120)
            c.pack(side="left", padx=10, pady=4, fill="both", expand=True)
            bg, fg = p_colors[i], p_fgs[i]
            short  = name if len(name) <= 22 else name[:19] + "..."
            trend_txt, trend_fg = self._trend_text(qty, prev_map.get(name, (0, 0))[0])
            def _draw_podium(ev, c=c, bg=bg, fg=fg, medal=medals[i], short=short,
                             qty=qty, rev=rev, trend_txt=trend_txt, trend_fg=trend_fg):
                c.delete("all")
                w, h = c.winfo_width(), c.winfo_height()
                if w < 10: return
                r = 16
                c.create_polygon(r,0, w-r,0, w,0, w,r, w,h-r, w,h, w-r,h,
                                 r,h, 0,h, 0,h-r, 0,r, 0,0,
                                 smooth=True, fill=bg, outline=bg)
                c.create_text(w//2, 16, text=f"{medal}  {short}",
                              font=(FONT, 12, "bold"), fill=fg, anchor="n")
                c.create_text(w//2, 50, text=f"{int(qty):,} sold",
                              font=(FONT, 11), fill=fg, anchor="n")
                c.create_text(w//2, 72, text=f"₱{rev:,.2f}",
                              font=(FONT, 13, "bold"), fill=fg, anchor="n")
                if trend_txt:
                    c.create_text(w//2, 96, text=trend_txt,
                                  font=(FONT, 10, "bold"),
                                  fill=trend_fg if trend_fg else fg, anchor="n")
            c.bind("<Configure>", _draw_podium)
            c.after(50, lambda c=c: c.event_generate("<Configure>"))

        # ── Progress bar table ───────────────────────────────────────────────
        tk.Label(self.graph_frame, text="Product Rankings",
                 font=(FONT, 14, "bold"), bg=CONTENT, fg=SIDEBAR).pack(anchor="w", pady=(8, 6))

        for i, (name, qty, rev) in enumerate(zip(products, quantities, sales)):
            row = tk.Frame(self.graph_frame, bg=ROW_ALT if i % 2 == 0 else CONTENT)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=f"{medals[i] if i < 3 else str(i+1)+'.':>3}",
                     font=(FONT, 12, "bold"), bg=row.cget("bg"), fg=SIDEBAR,
                     width=3).pack(side="left", padx=(8, 4))
            short = name if len(name) <= 28 else name[:25] + "..."
            tk.Label(row, text=short, font=(FONT, 12), bg=row.cget("bg"),
                     fg=FG_DARK, width=28, anchor="w").pack(side="left", padx=(0, 12))

            # qty bar
            bar_frame = tk.Frame(row, bg=row.cget("bg"))
            bar_frame.pack(side="left", padx=(0, 16))
            tk.Label(bar_frame, text="Qty", font=(FONT, 10), bg=row.cget("bg"),
                     fg=FG_DARK).pack(anchor="w")
            bar_bg = tk.Frame(bar_frame, bg="#e0d0c0", height=12, width=160)
            bar_bg.pack()
            bar_bg.pack_propagate(False)
            fill_w = max(4, int(160 * qty / max_qty))
            tk.Frame(bar_bg, bg=ACCENT, width=fill_w, height=12).place(x=0, y=0)
            tk.Label(bar_frame, text=f"{int(qty):,}", font=(FONT, 10, "bold"),
                     bg=row.cget("bg"), fg=FG_DARK).pack(anchor="e")

            # revenue bar
            rev_frame = tk.Frame(row, bg=row.cget("bg"))
            rev_frame.pack(side="left")
            tk.Label(rev_frame, text="Revenue", font=(FONT, 10), bg=row.cget("bg"),
                     fg=FG_DARK).pack(anchor="w")
            rev_bg = tk.Frame(rev_frame, bg="#e0d0c0", height=12, width=160)
            rev_bg.pack()
            rev_bg.pack_propagate(False)
            fill_r = max(4, int(160 * rev / max_rev))
            tk.Frame(rev_bg, bg=SIDEBAR, width=fill_r, height=12).place(x=0, y=0)
            tk.Label(rev_frame, text=f"₱{rev:,.2f}", font=(FONT, 10, "bold"),
                     bg=row.cget("bg"), fg=FG_DARK).pack(anchor="e")

            # trend indicator
            trend_txt, trend_fg = self._trend_text(qty, prev_map.get(name, (0, 0))[0])
            if trend_txt:
                tk.Label(row, text=trend_txt, font=(FONT, 11, "bold"),
                         bg=row.cget("bg"), fg=trend_fg).pack(side="left", padx=(12, 0))

        # ── Chart buttons ────────────────────────────────────────────────────
        fig = charts.build_top_products_figure(products, quantities, sales, title,
                                               self.root.winfo_screenwidth())
        btn_row = tk.Frame(self.graph_frame, bg=CONTENT)
        btn_row.pack(pady=(16, 8))
        self._themed_button(btn_row, "📊  View Interactive Chart",
                            lambda: charts.open_top_products_chart(fig))
        self._themed_button(btn_row, "📈  View Sales Progression",
                            lambda: charts.open_sales_time_series(period, self.root.winfo_screenwidth()),
                            primary=False)

    # ── Revenue Analysis ──────────────────────────────────────────────────────

    def show_revenue_analysis(self):
        self.clear_content()
        if hasattr(self, 'header_label'):
            self.header_label.config(text="💰  Revenue Analysis")
        self._section_title(self.content_frame, "Revenue Analysis")

        self.revenue_period_var = tk.StringVar(value="daily")
        self._period_selector(self.content_frame, self.revenue_period_var,
                              [("Daily", "daily"), ("Weekly", "weekly"), ("Monthly", "monthly")],
                              lambda: self.update_revenue_analysis(self.revenue_period_var.get()))

        self.revenue_frame = tk.Frame(self.content_frame, bg=CONTENT)
        self.revenue_frame.pack(fill="both", expand=True)
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
            tk.Label(self.revenue_frame, text="No sales data available for this period.",
                     font=(FONT, 13), bg=CONTENT, fg=FG_DARK).pack(pady=40)
            return

        total_rev = sum(r[3] for r in results)
        total_qty = sum(r[2] for r in results)
        avg_price = total_rev / total_qty if total_qty else 0
        top       = results[0]

        cards = tk.Frame(self.revenue_frame, bg=CONTENT)
        cards.pack(fill="x", pady=(0, 16))
        self._make_card(cards, 0, "💰  TOTAL REVENUE",  f"₱{total_rev:,.2f}")
        self._make_card(cards, 1, "📦  ITEMS SOLD",     str(int(total_qty)))
        self._make_card(cards, 2, "📊  AVG PRICE",      f"₱{avg_price:,.2f}", 18)
        top_name = top[0][:15] + "..." if len(top[0]) > 15 else top[0]
        self._make_card(cards, 3, f"🏆  TOP: {top_name}", f"₱{top[3]:,.0f}", 18)

        btn_row = tk.Frame(self.revenue_frame, bg=CONTENT)
        btn_row.pack(pady=(8, 16))
        self._themed_button(btn_row, "📊  View Interactive Revenue Chart",
                            lambda: charts.open_revenue_chart(results, title, self.root.winfo_screenwidth()))
        self._themed_button(btn_row, "📈  View Revenue Progression",
                            lambda: charts.open_revenue_time_series(period, self.root.winfo_screenwidth()),
                            primary=False)

        tk.Label(self.revenue_frame, text="Detailed Revenue Report",
                 font=(FONT, 14, "bold"), bg=CONTENT, fg=SIDEBAR).pack(anchor="w", pady=(0, 4))

        outer = tk.Frame(self.revenue_frame, bg=CONTENT)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=CONTENT, highlightthickness=0, height=280)
        sb     = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        sf     = tk.Frame(canvas, bg=CONTENT)
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        win = canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        headers = ["Product", "Unit Price", "Qty", "Revenue", "Avg/Unit", "Rev %"]
        widths  = [32, 12, 8, 14, 12, 8]
        for c, (h, w) in enumerate(zip(headers, widths)):
            tk.Label(sf, text=h, font=(FONT, 12, "bold"), bg=HDR_BG,
                     fg=FG_LIGHT, width=w, relief="flat", padx=8, pady=8,
                     anchor="w").grid(row=0, column=c, sticky="ew", padx=1, pady=1)

        for idx, data in enumerate(results[:20], 1):
            bg  = ROW_ALT if idx % 2 == 0 else CONTENT
            pct = data[3] / total_rev * 100 if total_rev else 0
            name = data[0][:30] + "..." if len(data[0]) > 30 else data[0]
            row_vals = [name, f"₱{data[1]:.0f}", str(int(data[2])),
                        f"₱{data[3]:.0f}", f"₱{data[5]:.0f}", f"{pct:.1f}%"]
            for c, (val, w) in enumerate(zip(row_vals, widths)):
                tk.Label(sf, text=val, font=(FONT, 12), bg=bg,
                         fg=FG_DARK, width=w, relief="flat", padx=8, pady=6,
                         anchor="w").grid(row=idx, column=c, sticky="ew", padx=1, pady=1)
