import tkinter as tk
from tkinter import messagebox
import os
import sys
import subprocess
from dashboard_views import DashboardViews
import export_reports


class Dashboard(DashboardViews):
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Dashboard - Chizzling POS")
        self.root.state('zoomed')
        self.root.configure(bg="#FAF3E1")
        self._build_layout()
        self.show_daily_sales()

    def _build_layout(self):
        main = tk.Frame(self.root, bg="#FAF3E1")
        main.pack(fill="both", expand=True)
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Header
        header = tk.Frame(main, bg="#FF6600", height=80)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        tk.Label(header, text="SALES DASHBOARD", font=("Arial", 20, "bold"),
                 bg="#FF6600", fg="white").pack(expand=True)

        # Nav buttons
        nav = tk.Frame(main, bg="#FAF3E1", height=80)
        nav.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        nav.grid_propagate(False)
        nav.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        buttons = [
            ("Daily Sales",       self.show_daily_sales,          "#28A745", "white"),
            ("Weekly Sales",      self.show_weekly_sales,         "#007BFF", "white"),
            ("Top Products",      self.show_top_products,         "#FFC107", "black"),
            ("Revenue Analysis",  self.show_revenue_analysis,     "#17A2B8", "white"),
            ("View Transactions", self.open_transaction_analytics,"#6F42C1", "white"),
            ("Export Report",     self.open_export_dialog,        "#FF6600", "white"),
            ("Archive Sales",     self.open_sales_archive,        "#5A6268", "white"),
            ("User Management",   self.open_user_management,      "#343A40", "white"),
            ("Logout",            self.logout_and_redirect,       "#DC3545", "white"),
        ]
        for col, (text, cmd, bg, fg) in enumerate(buttons):
            tk.Button(nav, text=text, command=cmd, bg=bg, fg=fg,
                      font=("Arial", 12, "bold"), height=2
                      ).grid(row=0, column=col, sticky="ew", padx=3)
        nav.grid_columnconfigure(tuple(range(len(buttons))), weight=1)

        # Content area
        self.content_frame = tk.Frame(main, bg="#FFFFFF", bd=2, relief="raised")
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def open_export_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Export Sales Report")
        win.geometry("340x260")
        win.resizable(False, False)
        win.configure(bg="#FAF3E1")
        win.grab_set()

        tk.Label(win, text="Export Sales Report", font=("Arial", 14, "bold"),
                 bg="#FAF3E1", fg="#FF6600").pack(pady=(20, 5))

        tk.Label(win, text="Select Period:", font=("Arial", 11), bg="#FAF3E1").pack()
        period_var = tk.StringVar(value="daily")
        period_frame = tk.Frame(win, bg="#FAF3E1")
        period_frame.pack(pady=5)
        for text, val in [("Daily", "daily"), ("Weekly", "weekly"), ("Monthly", "monthly")]:
            tk.Radiobutton(period_frame, text=text, variable=period_var, value=val,
                           bg="#FAF3E1", font=("Arial", 11)).pack(side="left", padx=8)

        tk.Label(win, text="Select Format:", font=("Arial", 11), bg="#FAF3E1").pack(pady=(10, 0))
        fmt_frame = tk.Frame(win, bg="#FAF3E1")
        fmt_frame.pack(pady=5)
        tk.Button(fmt_frame, text="📄 Export CSV",
                  command=lambda: [win.destroy(), export_reports.export_csv(period_var.get())],
                  bg="#28A745", fg="white", font=("Arial", 12, "bold"),
                  width=14, height=2).pack(side="left", padx=8)
        tk.Button(fmt_frame, text="🖨 Export PDF",
                  command=lambda: [win.destroy(), export_reports.export_pdf(period_var.get())],
                  bg="#17A2B8", fg="white", font=("Arial", 12, "bold"),
                  width=14, height=2).pack(side="left", padx=8)

        tk.Button(win, text="Cancel", command=win.destroy,
                  bg="#6C757D", fg="white", font=("Arial", 10
                  )).pack(pady=(15, 0))

    def open_sales_archive(self):
        try:
            subprocess.Popen([sys.executable, "sales_archive.py"],
                             cwd=os.path.dirname(__file__))
        except Exception as e:
            print(f"Error opening sales archive: {e}")

    def open_transaction_analytics(self):
        try:
            subprocess.Popen([sys.executable, "transaction_analytics_app.py"],
                             cwd=os.path.dirname(__file__))
        except Exception as e:
            print(f"Error opening transaction analytics: {e}")

    def open_user_management(self):
        from user_management import UserManagement
        win = tk.Toplevel(self.root)
        UserManagement(win)

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
