import tkinter as tk
import os
import subprocess
from dashboard_views import DashboardViews


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
            ("Logout",            self.logout_and_redirect,       "#DC3545", "white"),
        ]
        for col, (text, cmd, bg, fg) in enumerate(buttons):
            tk.Button(nav, text=text, command=cmd, bg=bg, fg=fg,
                      font=("Arial", 12, "bold"), height=2
                      ).grid(row=0, column=col, sticky="ew", padx=3)

        # Content area
        self.content_frame = tk.Frame(main, bg="#FFFFFF", bd=2, relief="raised")
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def open_transaction_analytics(self):
        try:
            subprocess.Popen(["python", "transaction_analytics_app.py"],
                             cwd=os.path.dirname(__file__))
        except Exception as e:
            print(f"Error opening transaction analytics: {e}")

    def logout_and_redirect(self):
        try:
            self.root.destroy()
            subprocess.Popen(["python", "LoginPage.py"],
                             cwd=os.path.dirname(__file__))
        except Exception as e:
            print(f"Error during logout: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()
