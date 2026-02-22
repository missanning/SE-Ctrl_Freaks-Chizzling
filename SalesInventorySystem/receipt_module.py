import tkinter as tk
from tkinter import messagebox, scrolledtext
from datetime import datetime
import win32print
import win32ui
import os

def generate_receipt_text(transaction_id, date, cart, total, change):
    receipt = f"""{'='*32}
      CHIZZLING POS
{'='*30}
Date: {date}
Transaction ID: {transaction_id}
{'='*30}
"""
    for item in cart:
        receipt += f"{item[1]}\n  {item[2]} x {item[3]/item[2]:.2f} = {item[3]:.2f}\n"
    
    receipt += f"""{'='*30}
Total: {total:.2f}
Payment: {total + change:.2f}
Change: {change:.2f}
{'='*30}
  Thank you for your purchase!
{'='*30}"""
    return receipt

def save_receipt(receipt, transaction_id):
    os.makedirs("SalesInventorySystem/Receipts after Sale", exist_ok=True)
    receipt_file = f"SalesInventorySystem/Receipts after Sale/receipt_{transaction_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(receipt_file, 'w') as f:
        f.write(receipt)

def print_receipt(receipt):
    try:
        printer_name = win32print.GetDefaultPrinter()
        hprinter = win32print.OpenPrinter(printer_name)
        
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        hdc.StartDoc("Receipt")
        hdc.StartPage()
        
        font = win32ui.CreateFont({"name": "Courier New", "height": 40})
        hdc.SelectObject(font)
        
        y = 100
        for line in receipt.split('\n'):
            hdc.TextOut(100, y, line)
            y += 50
        
        hdc.EndPage()
        hdc.EndDoc()
        win32print.ClosePrinter(hprinter)
        
        messagebox.showinfo("Success", "Receipt sent to printer")
    except Exception as e:
        messagebox.showerror("Print Error", f"Failed to print: {str(e)}")

def show_receipt_window(root, transaction_id, date, cart, total, change):
    receipt = generate_receipt_text(transaction_id, date, cart, total, change)
    save_receipt(receipt, transaction_id)
    
    receipt_window = tk.Toplevel(root)
    receipt_window.title("Receipt")
    receipt_window.geometry("320x450")

    receipt_text = scrolledtext.ScrolledText(receipt_window, width=32, height=22, font=('Courier', 9))
    receipt_text.pack(padx=10, pady=10)

    receipt_text.insert(tk.END, receipt)
    receipt_text.config(state=tk.DISABLED)

    tk.Button(receipt_window, text="Print Receipt", command=lambda: print_receipt(receipt)).pack(pady=5)
    tk.Button(receipt_window, text="Close", command=receipt_window.destroy).pack(pady=5)
