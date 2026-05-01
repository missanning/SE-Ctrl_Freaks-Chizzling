import tkinter as tk
from datetime import datetime

WHITE      = "#FFFFFF"
PRIMARY    = "#F5A623"
PRIMARY_LT = "#FFF0D0"
BG         = "#FFF8EE"
TEXT_DARK  = "#3B1F0A"
TEXT_MID   = "#7A4F1E"
TEXT_MUTED = "#B07840"
BORDER     = "#FFD966"
RED        = "#FA5252"
GREEN      = "#40C057"
FONT_FAM   = "Segoe UI"
FONT_TITLE = (FONT_FAM, 14, "bold")
FONT_BOLD  = (FONT_FAM, 12, "bold")
FONT_BODY  = (FONT_FAM, 12)
FONT_SMALL = (FONT_FAM, 10)


class CartManager:
    def __init__(self, parent, pos_instance):
        self.parent = parent
        self.pos    = pos_instance
        self.cart   = []
        self._total = 0
        self.create_cart_panel()

    def create_cart_panel(self):
        right = tk.Frame(self.parent, bg=WHITE, width=380,
                         highlightbackground=BORDER, highlightthickness=1)
        right.pack(fill="both", expand=True)
        right.pack_propagate(False)
        self.right = right

        pad = dict(padx=16)

        # Title
        hdr = tk.Frame(right, bg=WHITE)
        hdr.pack(fill="x", pady=(14, 6), **pad)
        tk.Label(hdr, text="Order Details", font=FONT_TITLE,
                 fg=TEXT_DARK, bg=WHITE).pack(side="left")

        # Cart scroll area
        cart_outer = tk.Frame(right, bg=WHITE)
        cart_outer.pack(fill="both", expand=True, **pad)

        self.cart_canvas = tk.Canvas(cart_outer, bg=WHITE, highlightthickness=0)
        cart_sb = tk.Scrollbar(cart_outer, orient="vertical", command=self.cart_canvas.yview)
        self.cart_canvas.configure(yscrollcommand=cart_sb.set)
        cart_sb.pack(side="right", fill="y")
        self.cart_canvas.pack(side="left", fill="both", expand=True)

        self.cart_inner = tk.Frame(self.cart_canvas, bg=WHITE)
        self._cart_window = self.cart_canvas.create_window((0, 0), window=self.cart_inner, anchor="nw")
        self.cart_inner.bind("<Configure>",
                             lambda _: self.cart_canvas.configure(
                                 scrollregion=self.cart_canvas.bbox("all")))
        self.cart_canvas.bind("<Configure>",
                              lambda e: self.cart_canvas.itemconfig(self._cart_window, width=e.width))

        # Divider
        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", pady=8)

        # Summary rows
        summary = tk.Frame(right, bg=WHITE)
        summary.pack(fill="x", **pad)
        self.lbl_subtotal = self._summary_row(summary, "Subtotal", "₱0.00")
        self.lbl_tax      = self._summary_row(summary, "Tax (12%)", "₱0.00")
        self.lbl_disc     = self._summary_row(summary, "Discount", "-₱0.00", val_fg=GREEN)

        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", pady=6)
        total_row = tk.Frame(right, bg=WHITE)
        total_row.pack(fill="x", **pad)
        tk.Label(total_row, text="Total", font=(FONT_FAM, 14, "bold"),
                 fg=TEXT_DARK, bg=WHITE).pack(side="left")
        self.lbl_total = tk.Label(total_row, text="₱0.00",
                                  font=(FONT_FAM, 14, "bold"), fg=TEXT_DARK, bg=WHITE)
        self.lbl_total.pack(side="right")

        # Payment
        pay_row = tk.Frame(right, bg=WHITE)
        pay_row.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(pay_row, text="Payment:", font=FONT_BOLD,
                 fg=TEXT_DARK, bg=WHITE).pack(side="left")
        self.payment_var = tk.StringVar()
        self.payment_var.trace("w", lambda *_: (self._validate_payment_input(), self._clear_error()))
        self.payment_entry = tk.Entry(pay_row, textvariable=self.payment_var,
                                      font=FONT_BOLD, fg=TEXT_DARK,
                                      relief="flat", bg=BG, width=12,
                                      highlightthickness=1, highlightbackground=BORDER)
        self.payment_entry.pack(side="right", ipady=5, padx=(6, 0))

        # Inline error
        self.error_lbl = tk.Label(right, text="", font=FONT_SMALL,
                                  fg=RED, bg=WHITE, wraplength=340, justify="left")
        self.error_lbl.pack(fill="x", padx=16)

        # Change
        change_row = tk.Frame(right, bg=WHITE)
        change_row.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(change_row, text="Change:", font=FONT_BOLD,
                 fg=TEXT_DARK, bg=WHITE).pack(side="left")
        self.lbl_change = tk.Label(change_row, text="₱0.00",
                                   font=(FONT_FAM, 13, "bold"), fg=GREEN, bg=WHITE)
        self.lbl_change.pack(side="right")

        # Buttons
        btn_row = tk.Frame(right, bg=WHITE)
        btn_row.pack(fill="x", padx=16, pady=(0, 16))
        tk.Button(btn_row, text="Cancel", command=self.cancel_order,
                  bg=BORDER, fg=TEXT_DARK, relief="flat",
                  font=FONT_BOLD, width=10, height=2).pack(side="left")
        tk.Button(btn_row, text="Place Order", command=self.confirm_payment,
                  bg=PRIMARY, fg=WHITE, relief="flat",
                  font=FONT_BOLD, width=18, height=2).pack(side="right")

        self._render_cart()

    def _summary_row(self, parent, label, value, val_fg=TEXT_DARK):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, font=FONT_BODY, fg=TEXT_DARK, bg=WHITE).pack(side="left")
        lbl = tk.Label(row, text=value, font=FONT_BODY, fg=val_fg, bg=WHITE)
        lbl.pack(side="right")
        return lbl

    def add_item(self, product_id, name, price, qty=1):
        ex = next((i for i in self.cart if i["id"] == product_id), None)
        if ex:
            ex["qty"] += qty
        else:
            self.cart.append({"id": product_id, "name": name, "price": price, "qty": qty})
        self._render_cart()

    def change_qty(self, pid, delta):
        ex = next((i for i in self.cart if i["id"] == pid), None)
        if not ex:
            return
        ex["qty"] += delta
        if ex["qty"] <= 0:
            self.cart = [i for i in self.cart if i["id"] != pid]
        self._render_cart()

    def remove_item(self, pid):
        self.cart = [i for i in self.cart if i["id"] != pid]
        self._render_cart()

    def clear_cart(self):
        self.cart = []
        self.payment_var.set("")
        self._render_cart()

    def cancel_order(self):
        if not self.cart:
            self._show_error("No items in cart to cancel.")
            return
        self.clear_cart()

    def _render_cart(self):
        for w in self.cart_inner.winfo_children():
            w.destroy()

        if not self.cart:
            tk.Label(self.cart_inner, text="Cart is empty",
                     font=FONT_BODY, fg=TEXT_DARK, bg=WHITE).pack(pady=20)
            self._update_summary()
            return

        for item in self.cart:
            row = tk.Frame(self.cart_inner, bg=PRIMARY_LT,
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", pady=3)

            # Qty controls packed first to always show
            ctrl = tk.Frame(row, bg=PRIMARY_LT)
            ctrl.pack(side="right", padx=8)
            minus = tk.Label(ctrl, text="−", font=(FONT_FAM, 15, "bold"),
                             bg=PRIMARY_LT, fg=TEXT_DARK, width=2, cursor="hand2")
            minus.pack(side="left", padx=1)
            minus.bind("<Button-1>", lambda _, pid=item["id"]: self.change_qty(pid, -1))

            tk.Label(ctrl, text=str(item["qty"]), font=FONT_BOLD,
                     fg=TEXT_DARK, bg=PRIMARY_LT, width=2).pack(side="left", padx=2)

            plus = tk.Label(ctrl, text="+", font=(FONT_FAM, 15, "bold"),
                            bg=PRIMARY_LT, fg=TEXT_DARK, width=2, cursor="hand2")
            plus.pack(side="left", padx=1)
            plus.bind("<Button-1>", lambda _, pid=item["id"]: self.change_qty(pid, 1))

            # Icon
            tk.Label(row, text="🍴", font=(FONT_FAM, 18),
                     bg=PRIMARY_LT, width=3).pack(side="left", padx=(6, 6), pady=6)

            # Info
            info = tk.Frame(row, bg=PRIMARY_LT)
            info.pack(side="left", fill="x", expand=True, pady=4)
            tk.Label(info, text=item["name"], font=FONT_BOLD,
                     fg=TEXT_DARK, bg=PRIMARY_LT, anchor="w").pack(fill="x")
            tk.Label(info, text=f"₱{item['price']:,.2f}", font=FONT_BODY,
                     fg=TEXT_DARK, bg=PRIMARY_LT, anchor="w").pack(fill="x")
            remove = tk.Label(info, text="Remove", font=FONT_SMALL,
                              fg=RED, bg=PRIMARY_LT, cursor="hand2", anchor="w")
            remove.pack(fill="x", pady=(0, 2))
            remove.bind("<Button-1>", lambda _, pid=item["id"]: self.remove_item(pid))

        self._update_summary()

    def _update_summary(self):
        subtotal = sum(i["price"] * i["qty"] for i in self.cart)
        tax      = subtotal * 0.12
        total    = subtotal + tax
        self.lbl_subtotal.config(text=f"₱{subtotal:,.2f}")
        self.lbl_tax.config(text=f"₱{tax:,.2f}")
        self.lbl_disc.config(text="-₱0.00")
        self.lbl_total.config(text=f"₱{total:,.2f}")
        self._total = total
        self._update_change()

    def _validate_payment_input(self):
        """Real-time validation: only allow digits and a single decimal point."""
        raw = self.payment_var.get()
        if not raw:
            self._update_change()
            return

        # Check for letters
        if any(c.isalpha() for c in raw):
            self._show_error("Letters are not allowed. Enter numbers only.")
            return

        # Check for symbols other than digits and a single dot
        allowed = set("0123456789.")
        bad_chars = [c for c in raw if c not in allowed]
        if bad_chars:
            self._show_error(f"Invalid character '{bad_chars[0]}'. Numbers only.")
            return

        # More than one decimal point
        if raw.count(".") > 1:
            self._show_error("Only one decimal point is allowed.")
            return

        # Valid number — update change display
        self._update_change()

    def _update_change(self):
        try:
            pay = float(self.payment_var.get())
        except ValueError:
            self.lbl_change.config(text="₱0.00", fg=TEXT_MUTED)
            return
        change = pay - self._total
        self.lbl_change.config(text=f"₱{change:,.2f}", fg=GREEN if change >= 0 else RED)

    def _show_error(self, msg):
        self.error_lbl.config(text=f"⚠ {msg}")
        self.payment_entry.config(highlightbackground=RED, highlightcolor=RED)
        self.right.after(3000, self._clear_error)

    def _clear_error(self):
        self.error_lbl.config(text="")
        self.payment_entry.config(highlightbackground=BORDER, highlightcolor=BORDER)

    def confirm_payment(self):
        if not self.cart:
            self._show_error("Cart is empty. Please add items first.")
            return

        raw = self.payment_var.get().strip()
        if not raw:
            self._show_error("Please enter a payment amount.")
            return
        if any(c.isalpha() for c in raw):
            self._show_error("Letters are not allowed. Enter numbers only.")
            return
        allowed = set("0123456789.")
        bad_chars = [c for c in raw if c not in allowed]
        if bad_chars:
            self._show_error(f"Invalid character '{bad_chars[0]}'. Numbers only.")
            return
        if raw.count(".") > 1:
            self._show_error("Only one decimal point is allowed.")
            return

        payment = float(raw)
        if payment <= 0:
            self._show_error("Payment amount must be greater than zero.")
            return
        if payment < self._total:
            self._show_error(f"Insufficient payment. Need ₱{self._total - payment:,.2f} more.")
            return

        self.pos.process_payment(self.cart, self._total, payment)
