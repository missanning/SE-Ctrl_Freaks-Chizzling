import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, timedelta
import os

def connect_db():
    db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
    return sqlite3.connect(db_path)

class TransactionAnalyticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transaction Analytics - Chizzling POS")
        self.root.state('zoomed')
        self.root.configure(bg="#FAF3E1")
        self.create_widgets()
        self.load_transactions()
    
    def create_widgets(self):
        # Main container
        main_container = tk.Frame(self.root, bg="#FAF3E1")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#FF6600", height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg="#FF6600")
        header_content.pack(expand=True)
        
        tk.Label(header_content, text="📊 TRANSACTION ANALYTICS", 
                font=("Arial", 20, "bold"), bg="#FF6600", fg="white").pack(pady=10)
        
        # Close button
        close_frame = tk.Frame(main_container, bg="#FAF3E1")
        close_frame.pack(fill="x", pady=(0, 10))
        
        tk.Button(close_frame, text="Close", command=self.root.destroy,
                 bg="#DC3545", fg="white", font=("Arial", 12, "bold"),
                 width=15, height=2).pack(side="right")
        
        # Date filter frame
        filter_frame = tk.Frame(main_container, bg="#F8F9FA", bd=2, relief="raised")
        filter_frame.pack(fill="x", pady=(0, 20))
        
        filter_content = tk.Frame(filter_frame, bg="#F8F9FA")
        filter_content.pack(pady=15)
        
        tk.Label(filter_content, text="📅 Filter by Date:", font=("Arial", 12, "bold"),
                bg="#F8F9FA").pack(side="left", padx=10)
        
        # Date picker with automatic refresh
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_picker = DateEntry(filter_content, textvariable=self.date_var,
                                   date_pattern='yyyy-mm-dd', width=12,
                                   background='darkblue', foreground='white',
                                   borderwidth=2)
        self.date_picker.pack(side="left", padx=10)
        
        # Bind date change event to auto-refresh
        self.date_picker.bind("<<DateEntrySelected>>", self.on_date_changed)
        
        tk.Button(filter_content, text="Today", command=self.set_today,
                 bg="#007BFF", fg="white", font=("Arial", 11, "bold"),
                 width=10, height=1).pack(side="left", padx=5)
        
        # Summary cards frame
        self.summary_frame = tk.Frame(main_container, bg="#FAF3E1")
        self.summary_frame.pack(fill="x", pady=(0, 20))
        
        # Transactions list frame
        list_container = tk.Frame(main_container, bg="#FFFFFF", bd=2, relief="raised")
        list_container.pack(fill="both", expand=True)
        
        list_header = tk.Frame(list_container, bg="#FFFFFF")
        list_header.pack(fill="x", pady=15)
        
        tk.Label(list_header, text="📋 Transaction Details", font=("Arial", 16, "bold"),
                bg="#FFFFFF").pack()
        
        # Create frame for treeview and scrollbar
        tree_frame = tk.Frame(list_container, bg="#FFFFFF")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create treeview for transactions
        columns = ("ID", "Date", "Time", "Total", "Payment", "Change")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Define headings
        self.tree.heading("ID", text="Transaction ID")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Time", text="Time")
        self.tree.heading("Total", text="Total (₱)")
        self.tree.heading("Payment", text="Payment (₱)")
        self.tree.heading("Change", text="Change (₱)")
        
        # Configure column widths
        self.tree.column("ID", width=120, anchor="center")
        self.tree.column("Date", width=120, anchor="center")
        self.tree.column("Time", width=120, anchor="center")
        self.tree.column("Total", width=150, anchor="e")
        self.tree.column("Payment", width=150, anchor="e")
        self.tree.column("Change", width=150, anchor="e")
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def on_date_changed(self, event=None):
        """Called automatically when date picker value changes"""
        self.load_transactions()
    
    def set_today(self):
        """Set date picker to today's date and refresh"""
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.load_transactions()
    
    def create_summary_cards(self, total_transactions, avg_transaction_value, total_sales):
        """Create summary cards showing key metrics"""
        # Clear existing cards
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        
        # Total Transactions Card
        trans_card = tk.Frame(self.summary_frame, bg="#007BFF", bd=3, relief="raised")
        trans_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(trans_card, text="🧾 TOTAL TRANSACTIONS", font=("Arial", 12, "bold"),
                bg="#007BFF", fg="white").pack(pady=(15, 5))
        tk.Label(trans_card, text=str(total_transactions), font=("Arial", 28, "bold"),
                bg="#007BFF", fg="white").pack(pady=(0, 15))
        
        # Average Transaction Value Card
        avg_card = tk.Frame(self.summary_frame, bg="#28A745", bd=3, relief="raised")
        avg_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(avg_card, text="📈 AVERAGE TRANSACTION", font=("Arial", 12, "bold"),
                bg="#28A745", fg="white").pack(pady=(15, 5))
        tk.Label(avg_card, text=f"₱{avg_transaction_value:.2f}", font=("Arial", 22, "bold"),
                bg="#28A745", fg="white").pack(pady=(0, 15))
        
        # Total Sales Card
        sales_card = tk.Frame(self.summary_frame, bg="#FFC107", bd=3, relief="raised")
        sales_card.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        tk.Label(sales_card, text="💰 TOTAL SALES", font=("Arial", 12, "bold"),
                bg="#FFC107", fg="white").pack(pady=(15, 5))
        tk.Label(sales_card, text=f"₱{total_sales:.2f}", font=("Arial", 22, "bold"),
                bg="#FFC107", fg="white").pack(pady=(0, 15))
    
    def load_transactions(self):
        """Load transactions for the selected date"""
        selected_date = self.date_var.get()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        conn = connect_db()
        cursor = conn.cursor()
        
        try:
            # Get transactions for selected date
            cursor.execute("""
                SELECT id, date, total, payment, change
                FROM transactions
                WHERE date LIKE ?
                ORDER BY date DESC
            """, (selected_date + '%',))
            
            transactions = cursor.fetchall()
            
            # Calculate metrics
            total_transactions = len(transactions)
            total_sales = sum(t[2] for t in transactions) if transactions else 0
            avg_transaction_value = total_sales / total_transactions if total_transactions > 0 else 0
            
            # Create summary cards
            self.create_summary_cards(total_transactions, avg_transaction_value, total_sales)
            
            # Populate treeview
            for transaction in transactions:
                trans_id, date_time, total, payment, change = transaction
                
                # Parse date and time
                try:
                    dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
                    date_str = dt.strftime("%Y-%m-%d")
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    date_str = date_time.split()[0] if ' ' in date_time else date_time
                    time_str = date_time.split()[1] if ' ' in date_time else "00:00:00"
                
                self.tree.insert("", "end", values=(
                    trans_id,
                    date_str,
                    time_str,
                    f"{total:.2f}",
                    f"{payment:.2f}",
                    f"{change:.2f}"
                ))
            
            # Show message if no transactions
            if not transactions:
                self.tree.insert("", "end", values=(
                    "No transactions", "found for", "selected date", "", "", ""
                ))
        
        except Exception as e:
            print(f"Error loading transactions: {e}")
            # Show error in summary cards
            self.create_summary_cards(0, 0, 0)
        
        finally:
            conn.close()

def main():
    root = tk.Tk()
    app = TransactionAnalyticsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()