import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime, timedelta
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot
import webbrowser
import tempfile
import subprocess

def connect_db():
    db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
    return sqlite3.connect(db_path)

class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Dashboard - Chizzling POS")
        # Set full screen mode
        self.root.state('zoomed')  # Windows full screen
        self.root.configure(bg="#FAF3E1")
        
        self.create_widgets()
        self.show_daily_sales()
    
    def create_widgets(self):
        # Main container with grid layout
        main_container = tk.Frame(self.root, bg="#FAF3E1")
        main_container.pack(fill="both", expand=True)
        main_container.grid_rowconfigure(2, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Header
        header = tk.Frame(main_container, bg="#FF6600", height=80)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        
        tk.Label(header, text="SALES DASHBOARD", font=("Arial", 20, "bold"),
                bg="#FF6600", fg="white").pack(expand=True)
        
        # Button Frame
        button_frame = tk.Frame(main_container, bg="#FAF3E1", height=80)
        button_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        button_frame.grid_propagate(False)
        button_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        
        tk.Button(button_frame, text="Daily Sales", command=self.show_daily_sales,
                 bg="#28A745", fg="white", font=("Arial", 12, "bold"), height=2).grid(row=0, column=0, sticky="ew", padx=3)
        
        tk.Button(button_frame, text="Weekly Sales", command=self.show_weekly_sales,
                 bg="#007BFF", fg="white", font=("Arial", 12, "bold"), height=2).grid(row=0, column=1, sticky="ew", padx=3)
        
        tk.Button(button_frame, text="Top Products", command=self.show_top_products,
                 bg="#FFC107", fg="black", font=("Arial", 12, "bold"), height=2).grid(row=0, column=2, sticky="ew", padx=3)
        
        tk.Button(button_frame, text="Revenue Analysis", command=self.show_revenue_analysis,
                 bg="#17A2B8", fg="white", font=("Arial", 12, "bold"), height=2).grid(row=0, column=3, sticky="ew", padx=3)
        
        tk.Button(button_frame, text="View Transactions", command=self.open_transaction_analytics,
                 bg="#6F42C1", fg="white", font=("Arial", 12, "bold"), height=2).grid(row=0, column=4, sticky="ew", padx=3)
        
        tk.Button(button_frame, text="Logout", command=self.logout_and_redirect,
                 bg="#DC3545", fg="white", font=("Arial", 12, "bold"), height=2).grid(row=0, column=5, sticky="ew", padx=3)
        
        # Content Frame
        self.content_frame = tk.Frame(main_container, bg="#FFFFFF", bd=2, relief="raised")
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
    
    def open_transaction_analytics(self):
        """Open transaction analytics in a new window"""
        try:
            # Launch the transaction analytics app as a separate process
            subprocess.Popen(["python", "transaction_analytics_app.py"], 
                           cwd=os.path.dirname(__file__))
        except Exception as e:
            print(f"Error opening transaction analytics: {e}")
    
    def logout_and_redirect(self):
        """Logout and redirect to login page"""
        try:
            # Close current window
            self.root.destroy()
            # Launch login page
            subprocess.Popen(["python", "LoginPage.py"], 
                           cwd=os.path.dirname(__file__))
        except Exception as e:
            print(f"Error during logout: {e}")
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_daily_sales(self):
        self.clear_content()
        
        # Title with better styling
        title_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        title_frame.pack(pady=15)
        
        tk.Label(title_frame, text="📊 DAILY SALES OVERVIEW", font=("Arial", 16, "bold"),
                bg="#FFFFFF", fg="#FF6600").pack()
        
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
        
        # Enhanced Summary Cards
        cards_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        cards_frame.pack(pady=20, padx=20, fill="x")
        
        # Daily Sales Card (Main Focus)
        sales_card = tk.Frame(cards_frame, bg="#28A745", bd=3, relief="raised")
        sales_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(sales_card, text="💰 TODAY'S TOTAL SALES", font=("Arial", 12, "bold"),
                bg="#28A745", fg="white").pack(pady=(15, 5))
        tk.Label(sales_card, text=f"₱{total_sales:.2f}", font=("Arial", 24, "bold"),
                bg="#28A745", fg="white").pack(pady=(0, 15))
        
        # Transactions Card
        trans_card = tk.Frame(cards_frame, bg="#007BFF", bd=3, relief="raised")
        trans_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(trans_card, text="🧾 TRANSACTIONS", font=("Arial", 12, "bold"),
                bg="#007BFF", fg="white").pack(pady=(15, 5))
        tk.Label(trans_card, text=str(transaction_count), font=("Arial", 24, "bold"),
                bg="#007BFF", fg="white").pack(pady=(0, 15))
        
        # Average Transaction Card
        avg_transaction = total_sales / transaction_count if transaction_count > 0 else 0
        avg_card = tk.Frame(cards_frame, bg="#FFC107", bd=3, relief="raised")
        avg_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(avg_card, text="📈 AVG TRANSACTION", font=("Arial", 12, "bold"),
                bg="#FFC107", fg="white").pack(pady=(15, 5))
        tk.Label(avg_card, text=f"₱{avg_transaction:.2f}", font=("Arial", 20, "bold"),
                bg="#FFC107", fg="white").pack(pady=(0, 15))
        
        # Date Display
        date_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        date_frame.pack(pady=10)
        
        tk.Label(date_frame, text=f"📅 Date: {today}", font=("Arial", 14, "bold"),
                bg="#FFFFFF", fg="#666666").pack()
        
        # Quick Performance Indicator
        performance_frame = tk.Frame(self.content_frame, bg="#F8F9FA", bd=1, relief="solid")
        performance_frame.pack(pady=15, padx=20, fill="x")
        
        tk.Label(performance_frame, text="📊 Quick Performance Summary", font=("Arial", 12, "bold"),
                bg="#F8F9FA").pack(pady=(10, 5))
        
        summary_text = f"Today you processed {transaction_count} transactions with total sales of ₱{total_sales:.2f}"
        if transaction_count > 0:
            summary_text += f"\nAverage transaction value: ₱{avg_transaction:.2f}"
        else:
            summary_text += "\nNo transactions recorded today."
            
        tk.Label(performance_frame, text=summary_text, font=("Arial", 11),
                bg="#F8F9FA", justify="center").pack(pady=(0, 10))
        
        conn.close()
    
    def show_weekly_sales(self):
        self.clear_content()
        
        # Title with better styling
        title_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        title_frame.pack(pady=15)
        
        tk.Label(title_frame, text="📈 WEEKLY SALES OVERVIEW", font=("Arial", 16, "bold"),
                bg="#FFFFFF", fg="#007BFF").pack()
        
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
        
        # Enhanced Weekly Summary Cards
        cards_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        cards_frame.pack(pady=20, padx=20, fill="x")
        
        # Weekly Sales Card (Main Focus)
        weekly_card = tk.Frame(cards_frame, bg="#007BFF", bd=3, relief="raised")
        weekly_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(weekly_card, text="💰 TOTAL WEEKLY SALES", font=("Arial", 12, "bold"),
                bg="#007BFF", fg="white").pack(pady=(15, 5))
        tk.Label(weekly_card, text=f"₱{total_sales:.2f}", font=("Arial", 24, "bold"),
                bg="#007BFF", fg="white").pack(pady=(0, 15))
        
        # Daily Average Card
        days_elapsed = (today - monday).days + 1
        avg_daily = total_sales / days_elapsed if days_elapsed > 0 else 0
        avg_card = tk.Frame(cards_frame, bg="#28A745", bd=3, relief="raised")
        avg_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(avg_card, text="📅 DAILY AVERAGE", font=("Arial", 12, "bold"),
                bg="#28A745", fg="white").pack(pady=(15, 5))
        tk.Label(avg_card, text=f"₱{avg_daily:.2f}", font=("Arial", 20, "bold"),
                bg="#28A745", fg="white").pack(pady=(0, 15))
        
        # Total Transactions Card
        trans_card = tk.Frame(cards_frame, bg="#FFC107", bd=3, relief="raised")
        trans_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(trans_card, text="🧾 TOTAL TRANSACTIONS", font=("Arial", 12, "bold"),
                bg="#FFC107", fg="white").pack(pady=(15, 5))
        tk.Label(trans_card, text=str(transaction_count), font=("Arial", 24, "bold"),
                bg="#FFC107", fg="white").pack(pady=(0, 15))
        
        # Week Period Display
        period_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        period_frame.pack(pady=10)
        
        tk.Label(period_frame, text=f"📅 Week Period: {date_from} to {date_to}", font=("Arial", 14, "bold"),
                bg="#FFFFFF", fg="#666666").pack()
        
        # Weekly Performance Summary
        performance_frame = tk.Frame(self.content_frame, bg="#F8F9FA", bd=1, relief="solid")
        performance_frame.pack(pady=15, padx=20, fill="x")
        
        tk.Label(performance_frame, text="📊 Weekly Performance Summary", font=("Arial", 12, "bold"),
                bg="#F8F9FA").pack(pady=(10, 5))
        
        summary_text = f"This week you processed {transaction_count} transactions with total sales of ₱{total_sales:.2f}\n"
        summary_text += f"Daily average: ₱{avg_daily:.2f} over {days_elapsed} days"
        if transaction_count > 0:
            avg_transaction = total_sales / transaction_count
            summary_text += f"\nAverage transaction value: ₱{avg_transaction:.2f}"
            
        tk.Label(performance_frame, text=summary_text, font=("Arial", 11),
                bg="#F8F9FA", justify="center").pack(pady=(0, 10))
        
        # Quick Daily Breakdown Table
        breakdown_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        breakdown_frame.pack(pady=15, padx=20, fill="both", expand=True)
        
        tk.Label(breakdown_frame, text="📈 Daily Breakdown", font=("Arial", 12, "bold"),
                bg="#FFFFFF").pack(pady=(0, 10))
        
        # Simplified daily breakdown
        cursor.execute("""
            SELECT DATE(date), COUNT(*), SUM(total)
            FROM transactions
            WHERE DATE(date) BETWEEN ? AND ?
            GROUP BY DATE(date)
            ORDER BY DATE(date) DESC
        """, (date_from, date_to))
        
        daily_data = cursor.fetchall()
        
        if daily_data:
            # Create a simple table view
            table_frame = tk.Frame(breakdown_frame, bg="#FFFFFF")
            table_frame.pack()
            
            # Headers
            tk.Label(table_frame, text="Date", font=("Arial", 11, "bold"), bg="#E9ECEF", 
                    width=15, relief="solid", bd=1).grid(row=0, column=0, sticky="ew")
            tk.Label(table_frame, text="Transactions", font=("Arial", 11, "bold"), bg="#E9ECEF", 
                    width=15, relief="solid", bd=1).grid(row=0, column=1, sticky="ew")
            tk.Label(table_frame, text="Sales", font=("Arial", 11, "bold"), bg="#E9ECEF", 
                    width=15, relief="solid", bd=1).grid(row=0, column=2, sticky="ew")
            
            # Data rows
            for i, (date, trans, sales) in enumerate(daily_data, 1):
                bg_color = "#F8F9FA" if i % 2 == 0 else "#FFFFFF"
                tk.Label(table_frame, text=date, font=("Arial", 10), bg=bg_color, 
                        width=15, relief="solid", bd=1).grid(row=i, column=0, sticky="ew")
                tk.Label(table_frame, text=str(trans), font=("Arial", 10), bg=bg_color, 
                        width=15, relief="solid", bd=1).grid(row=i, column=1, sticky="ew")
                tk.Label(table_frame, text=f"₱{sales:.2f}", font=("Arial", 10), bg=bg_color, 
                        width=15, relief="solid", bd=1).grid(row=i, column=2, sticky="ew")
        else:
            tk.Label(breakdown_frame, text="No sales data available for this week", 
                    font=("Arial", 11), bg="#FFFFFF", fg="#666666").pack(pady=20)
        
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
        
        # Graph container - responsive, full width
        graph_container = tk.Frame(self.content_frame, bg="#FFFFFF")
        graph_container.pack(fill="both", expand=True, padx=20, pady=10)
        graph_container.grid_rowconfigure(0, weight=1)
        graph_container.grid_columnconfigure(0, weight=1)
        
        self.graph_frame = tk.Frame(graph_container, bg="#FFFFFF")
        self.graph_frame.pack(fill="both", expand=True)
        
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
        
        # Create interactive Plotly charts
        self.create_plotly_charts(products, quantities, sales, title)
        
        # Add time-series chart button
        self.add_time_series_button(period)
    
    def create_plotly_charts(self, products, quantities, sales, title):
        # Create subplots using Plotly
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Top Products by Quantity', 'Top Products by Revenue'),
            horizontal_spacing=0.15
        )
        
        # Quantity chart (horizontal bar)
        fig.add_trace(
            go.Bar(
                y=products,
                x=quantities,
                orientation='h',
                name='Quantity',
                marker_color='#28A745',
                text=[f'{int(q)}' for q in quantities],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Quantity: %{x}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Revenue chart (horizontal bar)
        fig.add_trace(
            go.Bar(
                y=products,
                x=sales,
                orientation='h',
                name='Revenue',
                marker_color='#007BFF',
                text=[f'₱{s:.0f}' for s in sales],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Revenue: ₱%{x:.2f}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Update layout with dynamic sizing
        screen_width = self.root.winfo_screenwidth()
        chart_width = min(int(screen_width * 0.8), 1400)  # 80% of screen width, max 1400px
        
        fig.update_layout(
            title={
                'text': f'<b>{title}</b>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#333'}
            },
            showlegend=False,
            height=500,
            width=chart_width,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font={'family': 'Arial', 'size': 12},
            margin=dict(l=40, r=40, t=80, b=60)
        )
        
        # Update x-axes
        fig.update_xaxes(title_text="Quantity Sold", row=1, col=1, gridcolor='#E5E5E5')
        fig.update_xaxes(title_text="Revenue (₱)", row=1, col=2, gridcolor='#E5E5E5')
        
        # Update y-axes
        fig.update_yaxes(categoryorder='total ascending', row=1, col=1)
        fig.update_yaxes(categoryorder='total ascending', row=1, col=2)
        
        # Create button to open chart in browser - centered
        button_container = tk.Frame(self.graph_frame, bg="#FFFFFF")
        button_container.pack(pady=20, fill="x")
        
        chart_button = tk.Button(
            button_container,
            text="View Interactive Chart",
            command=lambda: self.open_plotly_chart(fig),
            bg="#FF6600",
            fg="white",
            font=("Arial", 14, "bold"),
            width=30,
            height=2,
            relief="raised",
            bd=3
        )
        chart_button.pack()
        
        # Create summary table
        self.create_summary_table(products, quantities, sales)
    
    def create_summary_table(self, products, quantities, sales):
        # Summary table frame - centered and responsive
        table_container = tk.Frame(self.graph_frame, bg="#FFFFFF")
        table_container.pack(pady=20, fill="x")
        
        table_frame = tk.Frame(table_container, bg="#F8F9FA", bd=2, relief="raised")
        table_frame.pack(expand=True)
        
        tk.Label(table_frame, text="Top Products Summary", font=("Arial", 14, "bold"),
                bg="#F8F9FA").pack(pady=15)
        
        # Create table headers
        headers_frame = tk.Frame(table_frame, bg="#F8F9FA")
        headers_frame.pack(fill="x", padx=20)
        
        tk.Label(headers_frame, text="Product", font=("Arial", 12, "bold"), bg="#E9ECEF",
                width=30, relief="solid", bd=1).grid(row=0, column=0, sticky="ew")
        tk.Label(headers_frame, text="Quantity", font=("Arial", 12, "bold"), bg="#E9ECEF",
                width=12, relief="solid", bd=1).grid(row=0, column=1, sticky="ew")
        tk.Label(headers_frame, text="Revenue", font=("Arial", 12, "bold"), bg="#E9ECEF",
                width=18, relief="solid", bd=1).grid(row=0, column=2, sticky="ew")
        
        # Add data rows
        for i, (product, qty, sale) in enumerate(zip(products, quantities, sales), 1):
            bg_color = "#FFFFFF" if i % 2 == 0 else "#F8F9FA"
            
            # Truncate long product names for table display
            display_name = product if len(product) <= 35 else product[:32] + "..."
            
            tk.Label(headers_frame, text=display_name, font=("Arial", 11), bg=bg_color,
                    width=30, relief="solid", bd=1, anchor="w").grid(row=i, column=0, sticky="ew")
            tk.Label(headers_frame, text=str(int(qty)), font=("Arial", 11), bg=bg_color,
                    width=12, relief="solid", bd=1).grid(row=i, column=1, sticky="ew")
            tk.Label(headers_frame, text=f"₱{sale:.2f}", font=("Arial", 11), bg=bg_color,
                    width=18, relief="solid", bd=1).grid(row=i, column=2, sticky="ew")
    
    def open_plotly_chart(self, fig):
        # Create temporary HTML file and open in browser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            html_content = plot(fig, output_type='div', include_plotlyjs=True)
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Chizzling POS - Sales Analytics</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #FAF3E1; }}
                    .header {{ background-color: #FF6600; color: white; padding: 20px; text-align: center; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Chizzling POS - Sales Analytics</h1>
                    <p>Interactive Sales Dashboard</p>
                </div>
                {html_content}
            </body>
            </html>
            """
            f.write(full_html)
            temp_path = f.name
        
        # Open in default browser
        webbrowser.open(f'file://{temp_path}')
    
    def show_revenue_analysis(self):
        self.clear_content()
        
        # Title with better styling
        title_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        title_frame.pack(pady=15)
        
        tk.Label(title_frame, text="💰 REVENUE ANALYSIS", font=("Arial", 16, "bold"),
                bg="#FFFFFF", fg="#17A2B8").pack()
        
        # Period selection
        period_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        period_frame.pack(pady=10)
        
        tk.Label(period_frame, text="Analysis Period:", font=("Arial", 11, "bold"), bg="#FFFFFF").pack(side="left", padx=5)
        
        period_var = tk.StringVar(value="daily")
        
        tk.Radiobutton(period_frame, text="Daily", variable=period_var, value="daily",
                      bg="#FFFFFF", command=lambda: self.update_revenue_analysis(period_var.get())).pack(side="left", padx=5)
        tk.Radiobutton(period_frame, text="Weekly", variable=period_var, value="weekly",
                      bg="#FFFFFF", command=lambda: self.update_revenue_analysis(period_var.get())).pack(side="left", padx=5)
        tk.Radiobutton(period_frame, text="Monthly", variable=period_var, value="monthly",
                      bg="#FFFFFF", command=lambda: self.update_revenue_analysis(period_var.get())).pack(side="left", padx=5)
        
        # Content container
        content_container = tk.Frame(self.content_frame, bg="#FFFFFF")
        content_container.pack(fill="both", expand=True, padx=20, pady=10)
        content_container.grid_rowconfigure(0, weight=1)
        content_container.grid_columnconfigure(0, weight=1)
        
        self.revenue_frame = tk.Frame(content_container, bg="#FFFFFF")
        self.revenue_frame.pack(fill="both", expand=True)
        
        self.revenue_period_var = period_var
        self.update_revenue_analysis("daily")
    
    def update_revenue_analysis(self, period):
        # Clear previous content
        for widget in self.revenue_frame.winfo_children():
            widget.destroy()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get date range
        today = datetime.now()
        if period == "daily":
            date_from = today.strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
            title = f"Today ({date_from})"
        elif period == "weekly":
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            date_from = monday.strftime("%Y-%m-%d")
            date_to = sunday.strftime("%Y-%m-%d")
            title = f"This Week ({date_from} to {date_to})"
        else:  # monthly
            first_day = today.replace(day=1)
            if today.month == 12:
                last_day = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = today.replace(month=today.month+1, day=1) - timedelta(days=1)
            date_from = first_day.strftime("%Y-%m-%d")
            date_to = last_day.strftime("%Y-%m-%d")
            title = f"This Month ({date_from} to {date_to})"
        
        # Get revenue data
        cursor.execute("""
            SELECT 
                p.name,
                p.price,
                SUM(ti.quantity) as total_quantity,
                SUM(ti.subtotal) as total_revenue,
                AVG(p.price) as avg_price,
                (SUM(ti.subtotal) / SUM(ti.quantity)) as avg_revenue_per_unit
            FROM transaction_items ti
            JOIN products p ON ti.product_id = p.id
            JOIN transactions t ON ti.transaction_id = t.id
            WHERE DATE(t.date) BETWEEN ? AND ?
            GROUP BY p.id, p.name, p.price
            HAVING total_quantity > 0
            ORDER BY total_revenue DESC
        """, (date_from, date_to))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            tk.Label(self.revenue_frame, text="No sales data available for this period",
                    font=("Arial", 14), bg="#FFFFFF", fg="#666666").pack(pady=50)
            return
        
        # Create summary cards
        self.create_revenue_summary(results, title)
        
        # Create detailed table
        self.create_revenue_table(results)
        
        # Create revenue chart
        self.create_revenue_chart(results, title)
        
        # Add time-series chart for revenue
        self.add_revenue_time_series_button(period)
    
    def create_revenue_summary(self, results, title):
        # Summary cards frame
        summary_frame = tk.Frame(self.revenue_frame, bg="#FFFFFF")
        summary_frame.pack(pady=20, padx=20, fill="x")
        
        # Calculate totals
        total_revenue = sum(row[3] for row in results)
        total_quantity = sum(row[2] for row in results)
        avg_price = total_revenue / total_quantity if total_quantity > 0 else 0
        
        # Total Revenue Card
        revenue_card = tk.Frame(summary_frame, bg="#28A745", bd=3, relief="raised")
        revenue_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(revenue_card, text="💰 TOTAL REVENUE", font=("Arial", 12, "bold"),
                bg="#28A745", fg="white").pack(pady=(15, 5))
        tk.Label(revenue_card, text=f"₱{total_revenue:.2f}", font=("Arial", 24, "bold"),
                bg="#28A745", fg="white").pack(pady=(0, 15))
        
        # Total Items Sold Card
        quantity_card = tk.Frame(summary_frame, bg="#007BFF", bd=3, relief="raised")
        quantity_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(quantity_card, text="📋 ITEMS SOLD", font=("Arial", 12, "bold"),
                bg="#007BFF", fg="white").pack(pady=(15, 5))
        tk.Label(quantity_card, text=str(int(total_quantity)), font=("Arial", 24, "bold"),
                bg="#007BFF", fg="white").pack(pady=(0, 15))
        
        # Average Price Card
        avg_card = tk.Frame(summary_frame, bg="#17A2B8", bd=3, relief="raised")
        avg_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(avg_card, text="📊 AVG PRICE", font=("Arial", 12, "bold"),
                bg="#17A2B8", fg="white").pack(pady=(15, 5))
        tk.Label(avg_card, text=f"₱{avg_price:.2f}", font=("Arial", 20, "bold"),
                bg="#17A2B8", fg="white").pack(pady=(0, 15))
        
        # Top Revenue Product Card
        if results:
            top_product = results[0]
            top_card = tk.Frame(summary_frame, bg="#FFC107", bd=3, relief="raised")
            top_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
            
            tk.Label(top_card, text="🏆 TOP PRODUCT", font=("Arial", 12, "bold"),
                    bg="#FFC107", fg="black").pack(pady=(15, 5))
            product_name = top_product[0][:15] + "..." if len(top_product[0]) > 15 else top_product[0]
            tk.Label(top_card, text=product_name, font=("Arial", 12, "bold"),
                    bg="#FFC107", fg="black").pack()
            tk.Label(top_card, text=f"₱{top_product[3]:.0f}", font=("Arial", 16, "bold"),
                    bg="#FFC107", fg="black").pack(pady=(0, 15))
    
    def create_revenue_table(self, results):
        # Table container
        table_container = tk.Frame(self.revenue_frame, bg="#FFFFFF")
        table_container.pack(pady=20, fill="both", expand=True)
        
        tk.Label(table_container, text="📋 Detailed Revenue Report", font=("Arial", 14, "bold"),
                bg="#FFFFFF").pack(pady=(0, 15))
        
        # Create scrollable frame
        canvas = tk.Canvas(table_container, bg="#FFFFFF", height=300)
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Table headers
        headers = ["Product", "Unit Price", "Qty Sold", "Total Revenue", "Avg Revenue/Unit", "Revenue %"]
        header_frame = tk.Frame(scrollable_frame, bg="#FFFFFF")
        header_frame.pack(fill="x", padx=10)
        
        for i, header in enumerate(headers):
            width = 25 if i == 0 else 15
            tk.Label(header_frame, text=header, font=("Arial", 10, "bold"), bg="#E9ECEF",
                    width=width, relief="solid", bd=1).grid(row=0, column=i, sticky="ew")
        
        # Calculate total revenue for percentage calculation
        total_revenue = sum(row[3] for row in results)
        
        # Data rows
        for row_idx, data in enumerate(results[:20], 1):  # Limit to top 20 products
            bg_color = "#F8F9FA" if row_idx % 2 == 0 else "#FFFFFF"
            revenue_percentage = (data[3] / total_revenue * 100) if total_revenue > 0 else 0
            
            # Product name (truncated)
            product_name = data[0][:30] + "..." if len(data[0]) > 30 else data[0]
            tk.Label(header_frame, text=product_name, font=("Arial", 9), bg=bg_color,
                    width=25, relief="solid", bd=1, anchor="w").grid(row=row_idx, column=0, sticky="ew")
            
            # Unit Price
            tk.Label(header_frame, text=f"₱{data[1]:.0f}", font=("Arial", 9), bg=bg_color,
                    width=15, relief="solid", bd=1).grid(row=row_idx, column=1, sticky="ew")
            
            # Quantity sold
            tk.Label(header_frame, text=str(int(data[2])), font=("Arial", 9), bg=bg_color,
                    width=15, relief="solid", bd=1).grid(row=row_idx, column=2, sticky="ew")
            
            # Total Revenue
            tk.Label(header_frame, text=f"₱{data[3]:.0f}", font=("Arial", 9, "bold"), 
                    bg=bg_color, fg="#28A745", width=15, relief="solid", bd=1).grid(row=row_idx, column=3, sticky="ew")
            
            # Average Revenue per Unit
            tk.Label(header_frame, text=f"₱{data[5]:.0f}", font=("Arial", 9), bg=bg_color,
                    width=15, relief="solid", bd=1).grid(row=row_idx, column=4, sticky="ew")
            
            # Revenue Percentage
            percentage_color = "#28A745" if revenue_percentage > 10 else "#FFC107" if revenue_percentage > 5 else "#6C757D"
            tk.Label(header_frame, text=f"{revenue_percentage:.1f}%", font=("Arial", 9, "bold"), 
                    bg=bg_color, fg=percentage_color, width=15, relief="solid", bd=1).grid(row=row_idx, column=5, sticky="ew")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_revenue_chart(self, results, title):
        # Chart button container
        chart_container = tk.Frame(self.revenue_frame, bg="#FFFFFF")
        chart_container.pack(pady=20, fill="x")
        
        # Create interactive chart button
        chart_button = tk.Button(
            chart_container,
            text="📊 View Interactive Revenue Chart",
            command=lambda: self.open_revenue_chart(results, title),
            bg="#17A2B8",
            fg="white",
            font=("Arial", 14, "bold"),
            width=40,
            height=2,
            relief="raised",
            bd=3
        )
        chart_button.pack()
    
    def open_revenue_chart(self, results, title):
        # Prepare data for chart (top 10 products)
        top_products = results[:10]
        products = [row[0] for row in top_products]
        revenues = [row[3] for row in top_products]
        quantities = [row[2] for row in top_products]
        prices = [row[1] for row in top_products]
        
        # Sort products by quantity for the quantity chart (descending order)
        quantity_sorted = sorted(zip(products, quantities), key=lambda x: x[1], reverse=True)
        quantity_products = [item[0] for item in quantity_sorted]
        quantity_values = [item[1] for item in quantity_sorted]
        
        # Create subplots
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Top Products by Revenue', 
                'Top Products by Quantity Sold',
                'Price vs Revenue Analysis',
                'Revenue Distribution'
            ),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "pie"}]]
        )
        
        # Revenue Chart (already sorted by revenue)
        fig.add_trace(
            go.Bar(
                x=products,
                y=revenues,
                name='Total Revenue',
                marker_color='#28A745',
                text=[f'₱{r:.0f}' for r in revenues],
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # Quantity Chart (sorted by quantity descending)
        fig.add_trace(
            go.Bar(
                x=quantity_products,
                y=quantity_values,
                name='Quantity Sold',
                marker_color='#007BFF',
                text=[f'{int(q)}' for q in quantity_values],
                textposition='outside'
            ),
            row=1, col=2
        )
        
        # Price vs Revenue Scatter
        fig.add_trace(
            go.Scatter(
                x=prices,
                y=revenues,
                mode='markers+text',
                name='Price vs Revenue',
                marker=dict(size=10, color='#FFC107'),
                text=[p[:10] + '...' if len(p) > 10 else p for p in products],
                textposition='top center'
            ),
            row=2, col=1
        )
        
        # Revenue Distribution Pie Chart
        fig.add_trace(
            go.Pie(
                labels=[p[:15] + '...' if len(p) > 15 else p for p in products],
                values=revenues,
                name="Revenue Share"
            ),
            row=2, col=2
        )
        
        # Update layout
        screen_width = self.root.winfo_screenwidth()
        chart_width = min(int(screen_width * 0.9), 1600)
        
        fig.update_layout(
            title={
                'text': f'<b>Revenue Analysis - {title}</b>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#333'}
            },
            showlegend=False,
            height=800,
            width=chart_width,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font={'family': 'Arial', 'size': 11}
        )
        
        # Update axes
        fig.update_xaxes(title_text="Products", row=1, col=1, tickangle=45)
        fig.update_yaxes(title_text="Revenue (₱)", row=1, col=1)
        fig.update_xaxes(title_text="Products", row=1, col=2, tickangle=45)
        fig.update_yaxes(title_text="Quantity Sold", row=1, col=2)
        fig.update_xaxes(title_text="Unit Price (₱)", row=2, col=1)
        fig.update_yaxes(title_text="Revenue (₱)", row=2, col=1)
        
        # Create and open HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            html_content = plot(fig, output_type='div', include_plotlyjs=True)
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Chizzling POS - Revenue Analysis</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #FAF3E1; }}
                    .header {{ background-color: #17A2B8; color: white; padding: 20px; text-align: center; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Chizzling POS - Revenue Analysis</h1>
                    <p>Sales Performance Dashboard</p>
                </div>
                {html_content}
            </body>
            </html>
            """
            f.write(full_html)
            temp_path = f.name
        
        # Open in default browser
        webbrowser.open(f'file://{temp_path}')

if __name__ == "__main__":
    root = tk.Tk()
    app = Dashboard(root)
    root.mainloop()
    def add_time_series_button(self, period):
        """Add button to view time-series sales progression chart"""
        button_container = tk.Frame(self.graph_frame, bg="#FFFFFF")
        button_container.pack(pady=10, fill="x")
        
        time_series_button = tk.Button(
            button_container,
            text="📈 View Sales Progression Chart",
            command=lambda: self.open_sales_time_series(period),
            bg="#28A745",
            fg="white",
            font=("Arial", 12, "bold"),
            width=30,
            height=2,
            relief="raised",
            bd=2
        )
        time_series_button.pack()
    
    def add_revenue_time_series_button(self, period):
        """Add button to view revenue time-series chart"""
        button_container = tk.Frame(self.revenue_frame, bg="#FFFFFF")
        button_container.pack(pady=10, fill="x")
        
        time_series_button = tk.Button(
            button_container,
            text="📈 View Revenue Progression Chart",
            command=lambda: self.open_revenue_time_series(period),
            bg="#28A745",
            fg="white",
            font=("Arial", 12, "bold"),
            width=30,
            height=2,
            relief="raised",
            bd=2
        )
        time_series_button.pack()
    
    def open_sales_time_series(self, period):
        """Create and display sales progression time-series chart"""
        conn = connect_db()
        cursor = conn.cursor()
        
        if period == "daily":
            dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
            title = "Daily Sales Progression (Last 7 Days)"
        else:
            dates = []
            for i in range(3, -1, -1):
                week_start = datetime.now() - timedelta(weeks=i, days=datetime.now().weekday())
                week_end = week_start + timedelta(days=6)
                dates.append((week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d"), f"Week {4-i}"))
            title = "Weekly Sales Progression (Last 4 Weeks)"
        
        sales_data = []
        transaction_data = []
        labels = []
        
        if period == "daily":
            for date in dates:
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(total), 0)
                    FROM transactions
                    WHERE DATE(date) = ?
                """, (date,))
                result = cursor.fetchone()
                transaction_data.append(result[0] if result[0] else 0)
                sales_data.append(result[1] if result[1] else 0)
                labels.append(datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d"))
        else:
            for start_date, end_date, week_label in dates:
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(total), 0)
                    FROM transactions
                    WHERE DATE(date) BETWEEN ? AND ?
                """, (start_date, end_date))
                result = cursor.fetchone()
                transaction_data.append(result[0] if result[0] else 0)
                sales_data.append(result[1] if result[1] else 0)
                labels.append(week_label)
        
        conn.close()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=labels,
            y=sales_data,
            mode='lines+markers+text',
            name='Total Sales',
            line=dict(color='#28A745', width=3),
            marker=dict(size=8, color='#28A745'),
            text=[f'₱{s:.0f}' for s in sales_data],
            textposition='top center',
            hovertemplate='<b>%{x}</b><br>Sales: ₱%{y:.2f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=labels,
            y=transaction_data,
            mode='lines+markers+text',
            name='Transactions',
            line=dict(color='#007BFF', width=3),
            marker=dict(size=8, color='#007BFF'),
            text=[str(t) for t in transaction_data],
            textposition='bottom center',
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>Transactions: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': f'<b>{title}</b>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#333'}
            },
            xaxis_title='Time Period',
            yaxis=dict(title='Sales (₱)', side='left', color='#28A745'),
            yaxis2=dict(title='Number of Transactions', side='right', overlaying='y', color='#007BFF'),
            height=500,
            width=min(int(self.root.winfo_screenwidth() * 0.8), 1200),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font={'family': 'Arial', 'size': 12},
            legend=dict(x=0.02, y=0.98),
            hovermode='x unified'
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            html_content = plot(fig, output_type='div', include_plotlyjs=True)
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Chizzling POS - Sales Progression</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #FAF3E1; }}
                    .header {{ background-color: #28A745; color: white; padding: 20px; text-align: center; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Chizzling POS - Sales Progression</h1>
                    <p>Time-Series Sales Analysis</p>
                </div>
                {html_content}
            </body>
            </html>
            """
            f.write(full_html)
            temp_path = f.name
        
        webbrowser.open(f'file://{temp_path}')
    
    def open_revenue_time_series(self, period):
        """Create and display revenue progression time-series chart"""
        conn = connect_db()
        cursor = conn.cursor()
        
        if period == "daily":
            dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
            title = "Daily Revenue Progression (Last 7 Days)"
        elif period == "weekly":
            dates = []
            for i in range(3, -1, -1):
                week_start = datetime.now() - timedelta(weeks=i, days=datetime.now().weekday())
                week_end = week_start + timedelta(days=6)
                dates.append((week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d"), f"Week {4-i}"))
            title = "Weekly Revenue Progression (Last 4 Weeks)"
        else:
            dates = []
            for i in range(5, -1, -1):
                month_date = datetime.now().replace(day=1) - timedelta(days=32*i)
                month_date = month_date.replace(day=1)
                if month_date.month == 12:
                    next_month = month_date.replace(year=month_date.year+1, month=1)
                else:
                    next_month = month_date.replace(month=month_date.month+1)
                month_end = next_month - timedelta(days=1)
                dates.append((month_date.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d"), month_date.strftime("%b %Y")))
            title = "Monthly Revenue Progression (Last 6 Months)"
        
        revenue_data = []
        quantity_data = []
        labels = []
        
        if period == "daily":
            for date in dates:
                cursor.execute("""
                    SELECT COALESCE(SUM(ti.subtotal), 0), COALESCE(SUM(ti.quantity), 0)
                    FROM transaction_items ti
                    JOIN transactions t ON ti.transaction_id = t.id
                    WHERE DATE(t.date) = ?
                """, (date,))
                result = cursor.fetchone()
                revenue_data.append(result[0] if result[0] else 0)
                quantity_data.append(result[1] if result[1] else 0)
                labels.append(datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d"))
        else:
            for start_date, end_date, period_label in dates:
                cursor.execute("""
                    SELECT COALESCE(SUM(ti.subtotal), 0), COALESCE(SUM(ti.quantity), 0)
                    FROM transaction_items ti
                    JOIN transactions t ON ti.transaction_id = t.id
                    WHERE DATE(t.date) BETWEEN ? AND ?
                """, (start_date, end_date))
                result = cursor.fetchone()
                revenue_data.append(result[0] if result[0] else 0)
                quantity_data.append(result[1] if result[1] else 0)
                labels.append(period_label)
        
        conn.close()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=labels,
            y=revenue_data,
            mode='lines+markers+text',
            name='Total Revenue',
            line=dict(color='#17A2B8', width=3),
            marker=dict(size=8, color='#17A2B8'),
            text=[f'₱{r:.0f}' for r in revenue_data],
            textposition='top center',
            hovertemplate='<b>%{x}</b><br>Revenue: ₱%{y:.2f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=labels,
            y=quantity_data,
            mode='lines+markers+text',
            name='Items Sold',
            line=dict(color='#FFC107', width=3),
            marker=dict(size=8, color='#FFC107'),
            text=[str(int(q)) for q in quantity_data],
            textposition='bottom center',
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>Items Sold: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': f'<b>{title}</b>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#333'}
            },
            xaxis_title='Time Period',
            yaxis=dict(title='Revenue (₱)', side='left', color='#17A2B8'),
            yaxis2=dict(title='Items Sold', side='right', overlaying='y', color='#FFC107'),
            height=500,
            width=min(int(self.root.winfo_screenwidth() * 0.8), 1200),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font={'family': 'Arial', 'size': 12},
            legend=dict(x=0.02, y=0.98),
            hovermode='x unified'
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            html_content = plot(fig, output_type='div', include_plotlyjs=True)
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Chizzling POS - Revenue Progression</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #FAF3E1; }}
                    .header {{ background-color: #17A2B8; color: white; padding: 20px; text-align: center; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Chizzling POS - Revenue Progression</h1>
                    <p>Time-Series Revenue Analysis</p>
                </div>
                {html_content}
            </body>
            </html>
            """
            f.write(full_html)
            temp_path = f.name
        
        webbrowser.open(f'file://{temp_path}')