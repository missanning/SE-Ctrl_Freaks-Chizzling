import tkinter as tk
from tkinter import messagebox
import os
import sys
import subprocess
from dashboard_views import DashboardViews
import export_reports


BG        = "#FFF8EE"
SIDEBAR   = "#7a3b10"
ACCENT    = "#f5a623"
YELLOW    = "#ffd966"
FG_LIGHT  = "#fff3e0"
FG_DARK   = "#3b1f0a"
HOVER     = "#5c2e00"
CONTENT   = "#ffffff"
FONT      = "Segoe UI"

class Dashboard(DashboardViews):
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Dashboard - Chizzling POS")
        self.root.state('zoomed')
        self.root.configure(bg=BG)
        self._proc_archive = None
        self._win_analytics = None
        self._win_user_mgmt = None
        self._active_btn = None
        self._build_layout()
        self.show_daily_sales()

    def _build_layout(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = tk.Frame(main, bg=SIDEBAR, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo area
        logo_frame = tk.Frame(sidebar, bg=SIDEBAR, pady=20)
        logo_frame.pack(fill="x")
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "LOGO.png")
        try:
            from PIL import Image, ImageTk
            img = Image.open(logo_path).resize((150, 150), Image.LANCZOS)
            self._logo_img = ImageTk.PhotoImage(img)
            tk.Label(logo_frame, image=self._logo_img, bg=SIDEBAR).pack()
        except Exception:
            pass
        tk.Label(logo_frame, text="Admin Dashboard", font=(FONT, 13, "bold"),
                 bg=SIDEBAR, fg=YELLOW).pack(pady=(6, 0))
        tk.Frame(sidebar, bg=ACCENT, height=2).pack(fill="x", padx=16, pady=(10, 0))

        # Nav items
        nav_items = [
            ("📊  Daily Sales",        self.show_daily_sales),
            ("📈  Weekly Sales",       self.show_weekly_sales),
            ("🏆  Top Products",       self.show_top_products),
            ("💰  Revenue Analysis",   self.show_revenue_analysis),
            ("🧾  View Transactions",  self.open_transaction_analytics),
            ("📤  Export Report",      self.open_export_dialog),
            ("🗂  Archive Sales",      self.open_sales_archive),
            ("👤  User Management",    self.open_user_management),
        ]
        self._nav_buttons = []
        nav_frame = tk.Frame(sidebar, bg=SIDEBAR)
        nav_frame.pack(fill="x", pady=(10, 0))
        for text, cmd in nav_items:
            btn = tk.Label(nav_frame, text=text, font=(FONT, 12),
                           bg=SIDEBAR, fg=FG_LIGHT, anchor="w",
                           padx=20, pady=10, cursor="hand2")
            btn.pack(fill="x")
            btn.bind("<Button-1>", lambda e, c=cmd, b=btn: self._nav_click(c, b))
            btn.bind("<Enter>",    lambda e, b=btn: b.config(bg=HOVER) if b != self._active_btn else None)
            btn.bind("<Leave>",    lambda e, b=btn: b.config(bg=SIDEBAR) if b != self._active_btn else None)
            self._nav_buttons.append(btn)

        # Logout at bottom
        tk.Frame(sidebar, bg=ACCENT, height=2).pack(fill="x", padx=16, side="bottom", pady=(0, 4))
        logout_btn = tk.Label(sidebar, text="🚪  Logout", font=(FONT, 12),
                              bg=SIDEBAR, fg="#ffaaaa", anchor="w",
                              padx=20, pady=10, cursor="hand2")
        logout_btn.pack(side="bottom", fill="x")
        logout_btn.bind("<Button-1>", lambda e: self.logout_and_redirect())
        logout_btn.bind("<Enter>",    lambda e: logout_btn.config(bg="#8b0000"))
        logout_btn.bind("<Leave>",    lambda e: logout_btn.config(bg=SIDEBAR))

        # ── Main content ─────────────────────────────────────────────────────
        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # Top header bar
        header = tk.Frame(right, bg=ACCENT, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        self.header_label = tk.Label(header, text="Sales Dashboard",
                                     font=(FONT, 18, "bold"), bg=ACCENT, fg=FG_DARK)
        self.header_label.pack(side="left", padx=24, pady=10)
        tk.Frame(right, bg=YELLOW, height=3).pack(fill="x")

        # Content area
        self.content_frame = tk.Frame(right, bg=CONTENT)
        self.content_frame.pack(fill="both", expand=True, padx=24, pady=20)

    def _nav_click(self, cmd, btn):
        if self._active_btn:
            self._active_btn.config(bg=SIDEBAR)
        self._active_btn = btn
        btn.config(bg=HOVER)
        cmd()

    def open_export_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Export Sales Report")
        win.geometry("340x260")
        win.resizable(False, False)
        win.configure(bg=BG)
        win.grab_set()
        win.update_idletasks()
        w, h = 420, 320
        x = (win.winfo_screenwidth() // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(win, text="Export Sales Report", font=(FONT, 14, "bold"),
                 bg=BG, fg=SIDEBAR).pack(pady=(20, 5))
        tk.Frame(win, bg=ACCENT, height=2).pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(win, text="Select Period:", font=(FONT, 11), bg=BG, fg=FG_DARK).pack()
        period_var = tk.StringVar(value="daily")
        period_frame = tk.Frame(win, bg=BG)
        period_frame.pack(pady=5)
        for text, val in [("Daily", "daily"), ("Weekly", "weekly"), ("Monthly", "monthly")]:
            tk.Radiobutton(period_frame, text=text, variable=period_var, value=val,
                           bg=BG, fg=FG_DARK, selectcolor=YELLOW,
                           font=(FONT, 11)).pack(side="left", padx=8)

        tk.Label(win, text="Select Format:", font=(FONT, 11), bg=BG, fg=FG_DARK).pack(pady=(10, 0))
        fmt_frame = tk.Frame(win, bg=BG)
        fmt_frame.pack(pady=5)
        tk.Button(fmt_frame, text="📄 Export CSV",
                  command=lambda: [win.destroy(), export_reports.export_csv(period_var.get())],
                  bg=SIDEBAR, fg=YELLOW, font=(FONT, 11, "bold"),
                  width=14, height=2, relief="flat").pack(side="left", padx=8)
        tk.Button(fmt_frame, text="🖨 Export PDF",
                  command=lambda: [win.destroy(), export_reports.export_pdf(period_var.get())],
                  bg=ACCENT, fg=FG_DARK, font=(FONT, 11, "bold"),
                  width=14, height=2, relief="flat").pack(side="left", padx=8)

        tk.Button(win, text="Cancel", command=win.destroy,
                  bg=BG, fg=SIDEBAR, font=(FONT, 10), relief="flat").pack(pady=(15, 0))

    def open_sales_archive(self):
        if hasattr(self, '_win_archive') and tk.Toplevel.winfo_exists(self._win_archive):
            self._win_archive.lift()
            self._win_archive.focus_force()
            return
        from sales_archive import SalesArchive
        self._win_archive = tk.Toplevel(self.root)
        SalesArchive(self._win_archive)

    def open_transaction_analytics(self):
        # If window exists and is still open, bring it to front
        if self._win_analytics and tk.Toplevel.winfo_exists(self._win_analytics):
            self._win_analytics.lift()
            self._win_analytics.focus_force()
            return
        # Otherwise open a new window
        from transaction_analytics_app import TransactionAnalyticsApp
        self._win_analytics = tk.Toplevel(self.root)
        TransactionAnalyticsApp(self._win_analytics)

    def open_user_management(self):
        if self._win_user_mgmt and tk.Toplevel.winfo_exists(self._win_user_mgmt):
            self._win_user_mgmt.lift()
            self._win_user_mgmt.focus_force()
            return
        from user_management import UserManagement
        self._win_user_mgmt = tk.Toplevel(self.root)
        UserManagement(self._win_user_mgmt)

    def logout_and_redirect(self):
        try:
            self.root.destroy()
            subprocess.Popen([sys.executable, "LoginPage.py"],
                             cwd=os.path.dirname(__file__))
        except Exception as e:
            print(f"Error during logout: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()
