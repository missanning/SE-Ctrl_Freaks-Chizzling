import tkinter as tk
import os
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

WHITE     = "#FFFFFF"
PRIMARY   = "#F5A623"
BG        = "#FFF8EE"
TEXT_DARK = "#3B1F0A"
BORDER    = "#FFD966"
RED       = "#FA5252"
FONT_FAM  = "Segoe UI"
FONT_BOLD = (FONT_FAM, 12, "bold")
FONT_BODY = (FONT_FAM, 12)

IMAGE_MAP = {
    "Nachos": "nachos.jpg",
    "Shawarma Rice": "shawarmarice.jpg",
    "Fries - Cheese": "fries.jpg",
    "Fries - Barbeque": "fries.jpg",
    "Fries - Sour and Cream": "fries.jpg",
    "Takoyaki - Cheese (5pcs)": "takoyakicheese.jpg",
    "Takoyaki - Ham and Cheese (5pcs)": "takoyakihamcheese.jpg",
    "Takoyaki - Crab (5pcs)": "takoyakicrab.jpg",
    "Takoyaki - Overload (7pcs)": "takoyakioverload.jpg",
    "Chicken Tenders": "chickentenderscheese.jpg",
    "Sisig Silog": "sisigsilog.jpg",
    "Chicken silog": "chicksilog.jpg",
    "Sizzling Sisig (Rice Meal)": "sizzlingsisig.jpg",
    "Sizzling Tofu (Rice Meal)": "sizzlingtofu.png",
    "Sizzling Liempo (Rice Meal)": "sizzlingliempo.jpg",
    "Sizzling Sisig": "sizzlingsisig.jpg",
    "Sizzling Tofu": "sizzlingtofu.png",
    "Sizzling Liempo": "sizzlingliempo.jpg",
    "Sisig and Liempo": "sisig_liempo.png",
    "Sisig and Tofu": "tofu_sisig.png",
    "Sizzling Liempo and Tofu": "liempo_tofu.png",
    "Red Horse 1 Litro": "redhorse.jpg",
    "Alfonso Light": "alfonsolight.jpg",
    "Gin Bilog": "ginbilog.jpg",
    "Gin Kwatro": "ginkwatro.jpg",
    "Pale Pilsen": "palepilsen.png",
    "Chocolate Milk Tea": "chocolate.png",
}
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "food @chizzlin")


class QuantityDialog:
    def __init__(self, parent, product, cart_manager, img_cache=None, pos=None):
        self.parent       = parent
        self.product      = product
        self.cart_manager = cart_manager
        self.pos          = pos
        self._img_cache   = img_cache or {}
        self.show_dialog()

    def show_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add to Cart")
        self.dialog.configure(bg=WHITE)
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center
        self.dialog.update_idletasks()
        w, h = 380, 460
        x = (self.dialog.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (h // 2)
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")

        pid, name, price, *_ = self.product

        # Product image
        IMG_W, IMG_H = 340, 200
        img_frame = tk.Frame(self.dialog, bg=BG, width=IMG_W, height=IMG_H)
        img_frame.pack(pady=(16, 0))
        img_frame.pack_propagate(False)

        photo = None
        if PIL_AVAILABLE:
            filename  = IMAGE_MAP.get(name, "no image.jpg")
            img_path  = os.path.join(ASSETS_DIR, filename)
            cache_key = (img_path, IMG_W, IMG_H)
            if cache_key not in self._img_cache:
                try:
                    pil_img = Image.open(img_path)
                    iw, ih  = pil_img.size
                    scale   = max(IMG_W / iw, IMG_H / ih)
                    nw, nh  = int(iw * scale), int(ih * scale)
                    pil_img = pil_img.resize((nw, nh), Image.LANCZOS)
                    left    = (nw - IMG_W) // 2
                    top     = (nh - IMG_H) // 2
                    pil_img = pil_img.crop((left, top, left + IMG_W, top + IMG_H))
                    self._img_cache[cache_key] = ImageTk.PhotoImage(pil_img)
                except Exception:
                    self._img_cache[cache_key] = None
            photo = self._img_cache[cache_key]

        if photo:
            lbl = tk.Label(img_frame, image=photo, bg=BG, borderwidth=0)
            lbl.image = photo
            lbl.place(relx=0.5, rely=0.5, anchor="center")
        else:
            tk.Label(img_frame, text="🍴", font=(FONT_FAM, 40),
                     bg=BG, fg=TEXT_DARK).place(relx=0.5, rely=0.5, anchor="center")

        # Name & price
        tk.Label(self.dialog, text=name, font=FONT_BOLD, fg=TEXT_DARK,
                 bg=WHITE, wraplength=340, justify="center").pack(pady=(12, 2))
        tk.Label(self.dialog, text=f"₱{price:,.2f}", font=(FONT_FAM, 13, "bold"),
                 fg=PRIMARY, bg=WHITE).pack(pady=(0, 10))

        # Quantity controls
        qty_frame = tk.Frame(self.dialog, bg=WHITE)
        qty_frame.pack(pady=8)
        tk.Label(qty_frame, text="Quantity:", font=FONT_BODY,
                 fg=TEXT_DARK, bg=WHITE).pack(side="left", padx=8)

        self.qty_var = tk.IntVar(value=1)

        minus = tk.Label(qty_frame, text="−", font=(FONT_FAM, 16, "bold"),
                         bg=BG, fg=TEXT_DARK, width=3, cursor="hand2",
                         highlightbackground=BORDER, highlightthickness=1)
        minus.pack(side="left", padx=2)
        minus.bind("<Button-1>", lambda _: self.qty_var.set(max(1, self.qty_var.get() - 1)))

        tk.Label(qty_frame, textvariable=self.qty_var, font=FONT_BOLD,
                 fg=TEXT_DARK, bg=WHITE, width=4,
                 highlightbackground=BORDER, highlightthickness=1).pack(side="left", padx=4)

        plus = tk.Label(qty_frame, text="+", font=(FONT_FAM, 16, "bold"),
                        bg=BG, fg=TEXT_DARK, width=3, cursor="hand2",
                        highlightbackground=BORDER, highlightthickness=1)
        plus.pack(side="left", padx=2)
        plus.bind("<Button-1>", lambda _: self.qty_var.set(self.qty_var.get() + 1))

        # Buttons
        btn_frame = tk.Frame(self.dialog, bg=WHITE)
        btn_frame.pack(pady=16)
        tk.Button(btn_frame, text="Add to Cart", command=self._add,
                  bg=PRIMARY, fg=WHITE, relief="flat",
                  font=FONT_BOLD, width=14, height=2).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Cancel", command=self.dialog.destroy,
                  bg=BORDER, fg=TEXT_DARK, relief="flat",
                  font=FONT_BOLD, width=10, height=2).pack(side="left", padx=8)

    def _add(self):
        pid, name, price, *_ = self.product
        qty = self.qty_var.get()
        # Run stock check through POS if available
        if self.pos:
            stock = self.pos._get_stock(pid)
            if stock <= 0:
                import tkinter.messagebox as mb
                mb.showerror("Out of Stock", f"'{name}' is currently out of stock.")
                return
            if qty > stock:
                import tkinter.messagebox as mb
                mb.showerror("Insufficient Stock", f"Only {stock} unit(s) available for '{name}'.")
                return
        self.cart_manager.add_item(pid, name, price, qty)
        self.dialog.destroy()
