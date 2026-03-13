import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

def connect_db():
    db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
    return sqlite3.connect(db_path)

class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Dashboard - Chizzling POS")
        self.root.geometry("1200x700")
        self.root.configure(bg="#FAF3E1")
        
        self.create_widgets()
        self.show_daily_sales()
    
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg="#FF6600", height=60)
        header.pack(fill="x")
        
        tk.Label(header, text="SALES DASHBOARD", font=("Arial", 18, "bold"),
                bg="#FF6600", fg="white").pack(pady=15)
        
        # Button Frame
        button_frame = tk.Frame(self.root, bg="#FAF3E1")
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Daily Sales", command=self.show_daily_sales,
                 bg="#28A745", fg="white", width=15, height=2).pack(side="left", padx=10)
        
        tk.Button(button_frame, text="Weekly Sales", command=self.show_weekly_sales,
                 bg="#007BFF", fg="white", width=15, height=2).pack(side="left", padx=10)
        
        tk.Button(button_frame, text="Top Products", command=self.show_top_products,
                 bg="#FFC107", fg="white", width=15, height=2).pack(side="left", padx=10)
        
        tk.Button(button_frame, text="Close", command=self.root.destroy,
                 bg="#DC3545", fg="white", width=15, height=2).pack(side="left", padx=10)
        
        # Content Frame
        self.content_frame = tk.Frame(self.root, bg="#FFFFFF", bd=2, relief="raised")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_daily_sales(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="DAILY SALES REPORT", font=("Arial", 14, "bold"),
                bg="#FFFFFF").pack(pady=10)
        
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get today's transactions
        cursor.execute("""
            SELECT COUNT(*), SUM(total), SUM(payment), SUM(change)
            FROM transactions
            WHERE date LIKE ?
        """, (today + '%',))
        
        result = cursor.fetchone()
        transaction_count = result[0] if result[0] else 0
        total_sales = result[1] if result[1] else 0.0
        total_payment = result[2] if result[2] else 0.0
        total_change = result[3] if result[3] else 0.0
        
        # Summary Frame
        summary_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        summary_frame.pack(pady=20)
        
        tk.Label(summary_frame, text=f"Date: {today}", font=("Arial", 12),
                bg="#FFFFFF").grid(row=0, column=0, columnspan=2, pady=5)
        
        tk.Label(summary_frame, text="Total Transactions:", font=("Arial", 11, "bold"),
                bg="#FFFFFF").grid(row=1, column=0, sticky="w", padx=20, pady=5)
        tk.Label(summary_frame, text=str(transaction_count), font=("Arial", 11),
                bg="#FFFFFF").grid(row=1, column=1, sticky="w", pady=5)
        
        tk.Label(summary_frame, text="Total Sales:", font=("Arial", 11, "bold"),
                bg="#FFFFFF").grid(row=2, column=0, sticky="w", padx=20, pady=5)
        tk.Label(summary_frame, text=f"₱{total_sales:.2f}", font=("Arial", 11),
                bg="#FFFFFF", fg="#28A745").grid(row=2, column=1, sticky="w", pady=5)
        
        tk.Label(summary_frame, text="Total Payment Received:", font=("Arial", 11, "bold"),
                bg="#FFFFFF").grid(row=3, column=0, sticky="w", padx=20, pady=5)
        tk.Label(summary_frame, text=f"₱{total_payment:.2f}", font=("Arial", 11),
                bg="#FFFFFF").grid(row=3, column=1, sticky="w", pady=5)
        
        tk.Label(summary_frame, text="Total Change Given:", font=("Arial", 11, "bold"),
                bg="#FFFFFF").grid(row=4, column=0, sticky="w", padx=20, pady=5)
        tk.Label(summary_frame, text=f"₱{total_change:.2f}", font=("Arial", 11),
                bg="#FFFFFF").grid(row=4, column=1, sticky="w", pady=5)
        
        # Transaction Details
        tk.Label(self.content_frame, text="Transaction Details", font=("Arial", 12, "bold"),
                bg="#FFFFFF").pack(pady=10)
        
        # Treeview for transactions
        tree_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        tree = ttk.Treeview(tree_frame, columns=("ID", "Time", "Total", "Payment", "Change"),
                           show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)
        
        tree.heading("ID", text="Transaction ID")
        tree.heading("Time", text="Time")
        tree.heading("Total", text="Total")
        tree.heading("Payment", text="Payment")
        tree.heading("Change", text="Change")
        
        tree.column("ID", width=100, anchor="center")
        tree.column("Time", width=150, anchor="center")
        tree.column("Total", width=100, anchor="e")
        tree.column("Payment", width=100, anchor="e")
        tree.column("Change", width=100, anchor="e")
        
        # Get transaction details
        cursor.execute("""
            SELECT id, substr(date, 12), total, payment, change
            FROM transactions
            WHERE date LIKE ?
            ORDER BY date DESC
        """, (today + '%',))
        
        for row in cursor.fetchall():
            tree.insert("", "end", values=(row[0], row[1], f"₱{row[2]:.2f}", 
                                          f"₱{row[3]:.2f}", f"₱{row[4]:.2f}"))
        
        tree.pack(fill="both", expand=True)
        
        conn.close()
    
    def show_weekly_sales(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="WEEKLY SALES REPORT", font=("Arial", 14, "bold"),
                bg="#FFFFFF").pack(pady=10)
        
        # Get current week (Monday to Sunday)
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        
        date_from = monday.strftime("%Y-%m-%d")
        date_to = sunday.strftime("%Y-%m-%d")
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get weekly summary
        cursor.execute("""
            SELECT COUNT(*), SUM(total), SUM(payment), SUM(change)
            FROM transactions
            WHERE DATE(date) BETWEEN ? AND ?
        """, (date_from, date_to))
        
        result = cursor.fetchone()
        transaction_count = result[0] if result[0] else 0
        total_sales = result[1] if result[1] else 0.0
        total_payment = result[2] if result[2] else 0.0
        total_change = result[3] if result[3] else 0.0
        
        # Summary Frame
        summary_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        summary_frame.pack(pady=20)
        
        tk.Label(summary_frame, text=f"Period: {date_from} to {date_to}", font=("Arial", 12),
                bg="#FFFFFF").grid(row=0, column=0, columnspan=2, pady=5)
        
        tk.Label(summary_frame, text="Total Transactions:", font=("Arial", 11, "bold"),
                bg="#FFFFFF").grid(row=1, column=0, sticky="w", padx=20, pady=5)
        tk.Label(summary_frame, text=str(transaction_count), font=("Arial", 11),
                bg="#FFFFFF").grid(row=1, column=1, sticky="w", pady=5)
        
        tk.Label(summary_frame, text="Total Sales:", font=("Arial", 11, "bold"),
                bg="#FFFFFF").grid(row=2, column=0, sticky="w", padx=20, pady=5)
        tk.Label(summary_frame, text=f"₱{total_sales:.2f}", font=("Arial", 11),
                bg="#FFFFFF", fg="#28A745").grid(row=2, column=1, sticky="w", pady=5)
        
        tk.Label(summary_frame, text="Average Daily Sales:", font=("Arial", 11, "bold"),
                bg="#FFFFFF").grid(row=3, column=0, sticky="w", padx=20, pady=5)
        days_elapsed = (today - monday).days + 1
        avg_daily = total_sales / days_elapsed if days_elapsed > 0 else 0
        tk.Label(summary_frame, text=f"₱{avg_daily:.2f}", font=("Arial", 11),
                bg="#FFFFFF").grid(row=3, column=1, sticky="w", pady=5)
        
        # Daily Breakdown
        tk.Label(self.content_frame, text="Daily Breakdown", font=("Arial", 12, "bold"),
                bg="#FFFFFF").pack(pady=10)
        
        # Treeview for daily breakdown
        tree_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        tree = ttk.Treeview(tree_frame, columns=("Date", "Transactions", "Total Sales"),
                           show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)
        
        tree.heading("Date", text="Date")
        tree.heading("Transactions", text="Transactions")
        tree.heading("Total Sales", text="Total Sales")
        
        tree.column("Date", width=200, anchor="center")
        tree.column("Transactions", width=150, anchor="center")
        tree.column("Total Sales", width=150, anchor="e")
        
        # Get daily breakdown
        cursor.execute("""
            SELECT DATE(date), COUNT(*), SUM(total)
            FROM transactions
            WHERE DATE(date) BETWEEN ? AND ?
            GROUP BY DATE(date)
            ORDER BY DATE(date) DESC
        """, (date_from, date_to))
        
        for row in cursor.fetchall():
            tree.insert("", "end", values=(row[0], row[1], f"₱{row[2]:.2f}"))
        
        tree.pack(fill="both", expand=True)
        
        conn.close()
    
    def show_top_products(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="TOP SELLING PRODUCTS", font=("Arial", 14, "bold"),
                bg="#FFFFFF").pack(pady=10)
        
        # Period selection
        period_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        period_frame.pack(pady=10)
        
        tk.Label(period_frame, text="View:", font=("Arial", 11), bg="#FFFFFF").pack(side="left", padx=5)
        
        period_var = tk.StringVar(value="daily")
        
        tk.Radiobutton(period_frame, text="Daily", variable=period_var, value="daily",
                      bg="#FFFFFF", command=lambda: self.update_top_products(period_var.get())).pack(side="left", padx=5)
        tk.Radiobutton(period_frame, text="Weekly", variable=period_var, value="weekly",
                      bg="#FFFFFF", command=lambda: self.update_top_products(period_var.get())).pack(side="left", padx=5)
        
        # Graph container - fixed size, centered
        graph_container = tk.Frame(self.content_frame, bg="#FFFFFF")
        graph_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.graph_frame = tk.Frame(graph_container, bg="#FFFFFF")
        self.graph_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.period_var = period_var
        self.update_top_products("daily")
    
    def update_top_products(self, period):
        # Clear previous graph
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get date range
        today = datetime.now()
        if period == "daily":
            date_from = today.strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
            title = f"Today ({date_from})"
        else:  # weekly
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            date_from = monday.strftime("%Y-%m-%d")
            date_to = sunday.strftime("%Y-%m-%d")
            title = f"This Week ({date_from} to {date_to})"
        
        # Get top products by quantity sold
        cursor.execute("""
            SELECT p.name, SUM(ti.quantity) as total_qty, SUM(ti.subtotal) as total_sales
            FROM transaction_items ti
            JOIN products p ON ti.product_id = p.id
            JOIN transactions t ON ti.transaction_id = t.id
            WHERE DATE(t.date) BETWEEN ? AND ?
            GROUP BY p.id, p.name
            ORDER BY total_qty DESC
            LIMIT 5
        """, (date_from, date_to))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            tk.Label(self.graph_frame, text="No sales data available for this period",
                    font=("Arial", 12), bg="#FFFFFF").pack(pady=50)
            return
        
        # Prepare data for graphs
        products = [row[0] for row in results]
        quantities = [row[1] for row in results]
        sales = [row[2] for row in results]
        
        # Don't truncate product names
        products_short = products
        
        # Create figure with two horizontal bar charts - adjusted size
        fig = Figure(figsize=(10, 5), facecolor='white', dpi=100)
        
        # Horizontal bar chart - Quantity Sold
        ax1 = fig.add_subplot(1, 2, 1)
        bars1 = ax1.barh(products_short, quantities, color='#28A745')
        ax1.set_xlabel('Quantity Sold', fontsize=10, fontweight='bold')
        ax1.set_title('By Quantity', fontsize=11, fontweight='bold', pad=10)
        ax1.invert_yaxis()
        ax1.tick_params(axis='y', labelsize=8)
        ax1.tick_params(axis='x', which='both', bottom=True, labelbottom=True)
        ax1.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        # Add value labels on bars with better positioning
        max_qty = max(quantities)
        for i, (bar, qty) in enumerate(zip(bars1, quantities)):
            ax1.text(qty + max_qty*0.02, i, f'{int(qty)}', va='center', ha='left', fontsize=9, fontweight='bold')
        
        # Extend x-axis limit to accommodate labels
        ax1.set_xlim(0, max_qty * 1.2)
        
        # Horizontal bar chart - Sales Revenue
        ax2 = fig.add_subplot(1, 2, 2)
        bars2 = ax2.barh(products_short, sales, color='#007BFF')
        ax2.set_xlabel('Sales Revenue (₱)', fontsize=10, fontweight='bold')
        ax2.set_title('By Revenue', fontsize=11, fontweight='bold', pad=10)
        ax2.invert_yaxis()
        ax2.tick_params(axis='y', labelsize=8)
        ax2.tick_params(axis='x', which='both', bottom=True, labelbottom=True)
        
        # Add value labels on bars with better positioning
        max_sale = max(sales)
        for i, (bar, sale) in enumerate(zip(bars2, sales)):
            ax2.text(sale + max_sale*0.02, i, f'₱{sale:.0f}', va='center', ha='left', fontsize=9, fontweight='bold')
        
        # Extend x-axis limit to accommodate labels
        ax2.set_xlim(0, max_sale * 1.2)
        
        fig.suptitle(title, fontsize=12, fontweight='bold', y=0.98)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95], w_pad=3)
        
        # Embed in tkinter with fixed size
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = Dashboard(root)
    root.mainloop()
