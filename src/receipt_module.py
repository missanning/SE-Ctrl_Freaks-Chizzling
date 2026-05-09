import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from datetime import datetime
import os
import threading
import time

def generate_receipt_text(transaction_id, date, cart, total, change):
    receipt = f"""{'='*30}
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
    os.makedirs("Receipts after Sale", exist_ok=True)
    receipt_file = f"Receipts after Sale/receipt_{transaction_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(receipt_file, 'w') as f:
        f.write(receipt)
    return receipt_file   # ← added: returns path so Save button can report it

# Virtual Printer
class VirtualPrinterWindow:
    BG          = "#FAF3E1"   # matches ChizzlingPOS background
    PRINTER_TOP = "#2C1A0E"
    PRINTER_MID = "#3D2512"
    PAPER_BG    = "#FFFEF7"
    PAPER_FG    = "#1A1A1A"
    SLOT_COLOR  = "#1A0E06"
    LED_ON      = "#00FF88"
    LED_OFF     = "#004422"
    BTN_CLOSE   = "#7B1E1E"
    BTN_FG      = "#FFFFFF"

    def __init__(self, root, receipt_text, transaction_id):
        self.root           = root
        self.receipt_text   = receipt_text
        self.transaction_id = transaction_id
        self.lines          = receipt_text.split("\n")
        self.printing       = False

        self._build_window()
        self._start_printing()

    # UI

    def _build_window(self):
        self.win = tk.Toplevel(self.root)
        self.win.title("Receipt")
        self.win.resizable(False, False)
        self.win.configure(bg=self.BG)
        self.win.grab_set()

        w, h = 420, 580
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        # ── Printer top panel ──
        top = tk.Frame(self.win, bg=self.PRINTER_TOP, pady=10)
        top.pack(fill="x")

        tk.Label(
            top, text="CHIZZLING POS  ·  Thermal Printer",
            font=("Courier New", 9, "bold"),
            bg=self.PRINTER_TOP, fg="#C8A96E"
        ).pack(side="left", padx=14)

        # LED indicator
        self.led_cv = tk.Canvas(top, width=16, height=16,
                                bg=self.PRINTER_TOP, highlightthickness=0)
        self.led_cv.pack(side="right", padx=14)
        self.led = self.led_cv.create_oval(2, 2, 14, 14,
                                           fill=self.LED_OFF, outline="")

        # ── Status + progress bar ──
        mid = tk.Frame(self.win, bg=self.PRINTER_MID, padx=14, pady=8)
        mid.pack(fill="x")

        self.status_var = tk.StringVar(value="● Warming up printer…")
        tk.Label(mid, textvariable=self.status_var,
                 font=("Courier New", 8),
                 bg=self.PRINTER_MID, fg=self.LED_ON
        ).pack(anchor="w")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Thermal.Horizontal.TProgressbar",
            troughcolor="#1A0E06",
            background=self.LED_ON,
            bordercolor=self.PRINTER_MID,
            lightcolor=self.LED_ON,
            darkcolor=self.LED_ON,
        )
        self.progress = ttk.Progressbar(
            mid, style="Thermal.Horizontal.TProgressbar",
            orient="horizontal", length=392, mode="determinate"
        )
        self.progress.pack(pady=(5, 0))

        # ── Paper exit slot (top) ──
        tk.Frame(self.win, bg=self.SLOT_COLOR, height=8).pack(fill="x")
        tk.Frame(self.win, bg="#2C1A0E",       height=4).pack(fill="x")

        # ── Paper area ──
        paper_wrap = tk.Frame(self.win, bg="#D4C5A9", padx=3, pady=0)
        paper_wrap.pack(fill="both", expand=True, padx=30)

        self.paper = scrolledtext.ScrolledText(
            paper_wrap,
            width=34, height=16,
            font=("Courier New", 11),
            bg=self.PAPER_BG,
            fg=self.PAPER_FG,
            relief="flat", bd=0,
            wrap="none",
            state="disabled",
            cursor="arrow",
            padx=10, pady=10,
            insertbackground=self.PAPER_BG,
        )
        self.paper.pack(fill="both", expand=True)

        # ── Paper exit slot (bottom) ──
        tk.Frame(self.win, bg="#2C1A0E",       height=4).pack(fill="x")
        tk.Frame(self.win, bg=self.SLOT_COLOR, height=8).pack(fill="x")

        # Buttons Close only (print & save happen automatically)
        btn_bar = tk.Frame(self.win, bg=self.BG, pady=12)
        btn_bar.pack(fill="x")

        self.btn_close = tk.Button(
            btn_bar, text="✕  Close",
            font=("Courier New", 9, "bold"),
            bg=self.BTN_CLOSE, fg=self.BTN_FG,
            activebackground="#9B2E2E", activeforeground="white",
            relief="flat", bd=0, padx=18, pady=8,
            cursor="hand2", state="disabled",
            command=self.win.destroy
        )
        self.btn_close.pack(pady=(0, 4))

    # Thermal print animation 

    def _start_printing(self):
        self.printing = True
        self._blink_led()
        threading.Thread(target=self._print_lines, daemon=True).start()

    def _blink_led(self):
        if not self.printing:
            return
        current    = self.led_cv.itemcget(self.led, "fill")
        next_color = self.LED_ON if current == self.LED_OFF else self.LED_OFF
        self.led_cv.itemconfig(self.led, fill=next_color)
        self.win.after(300, self._blink_led)

    def _print_lines(self):
        self._set_status("● Printing receipt…")
        time.sleep(0.35)

        try:
            self.root.bell()
        except Exception:
            pass

        total = max(len(self.lines), 1)
        for i, line in enumerate(self.lines):
            time.sleep(0.065)
            self._append_line(line)
            self._set_progress(int((i + 1) / total * 100))
            if i % 6 == 0:
                try:
                    self.root.bell()
                except Exception:
                    pass

        time.sleep(0.25)
        self.printing = False
        self._set_status("✔  Print complete — receipt ready")
        self._finalize()

    def _append_line(self, text):
        def _do():
            self.paper.config(state="normal")
            self.paper.insert(tk.END, text + "\n")
            self.paper.see(tk.END)
            self.paper.config(state="disabled")
        self.win.after(0, _do)

    def _set_status(self, msg):
        self.win.after(0, lambda: self.status_var.set(msg))

    def _set_progress(self, val):
        self.win.after(0, lambda: self.progress.configure(value=val))

    # If thermal printer is available
    #def print_receipt(receipt):
        #from escpos.printer import Usb
        #p = Usb(0x04b8, 0x0202)  # replace with your printer's vendor/product ID
        #p.text(receipt)
        #p.cut()
        #p.close()

    def _finalize(self):
        def _do():
            self.led_cv.itemconfig(self.led, fill=self.LED_ON)
            self.btn_close.config(state="normal")
            #print_receipt(self.receipt_text)
        self.win.after(0, _do)


def show_receipt_window(root, transaction_id, date, cart, total, change):
    receipt = generate_receipt_text(transaction_id, date, cart, total, change)
    save_receipt(receipt, transaction_id)          # auto-save on every transaction
    VirtualPrinterWindow(root, receipt, transaction_id)