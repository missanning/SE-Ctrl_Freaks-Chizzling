import tkinter as tk
import os
from quantity_dialog import QuantityDialog
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

BG       = "#FFF8EE"
WHITE    = "#FFFFFF"
PRIMARY  = "#F5A623"
TEXT_DARK = "#3B1F0A"
TEXT_MUTED = "#B07840"
BORDER   = "#FFD966"
FONT_FAM = "Segoe UI"
FONT_BOLD  = (FONT_FAM, 12, "bold")
FONT_BODY  = (FONT_FAM, 12)
FONT_TITLE = (FONT_FAM, 14, "bold")

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
    "Chocolate Milk Tea": "chocolate.png"
}
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "food @chizzlin")


class ProductDisplay:
    def __init__(self, parent, pos_instance):
        self.parent     = parent
        self.pos        = pos_instance
        self._img_cache = {}
        self.create_product_panel()

    def create_product_panel(self):
        panel = tk.Frame(self.parent, bg=BG)
        panel.pack(fill="both", expand=True, padx=(8, 8), pady=10)

        # Top row: count + search
        top_row = tk.Frame(panel, bg=BG)
        top_row.pack(fill="x", pady=(0, 10))
        self.prod_count_lbl = tk.Label(top_row, text="Products",
                                       font=FONT_TITLE, fg=TEXT_DARK, bg=BG)
        self.prod_count_lbl.pack(side="left")

        # Search bar container with rounded look
        search_container = tk.Frame(top_row, bg=WHITE,
                                    highlightbackground=BORDER,
                                    highlightthickness=2)
        search_container.pack(side="right", ipady=4, ipadx=6)

        tk.Label(search_container, text="🔍", bg=WHITE, fg=TEXT_DARK,
                 font=(FONT_FAM, 12)).pack(side="left", padx=(10, 4))

        self.search_var = tk.StringVar()
        self._search_job = None
        self.search_var.trace("w", lambda *_: self._schedule_filter())

        self._search_entry = tk.Entry(
            search_container, textvariable=self.search_var,
            bg=WHITE, relief="flat", font=FONT_BODY,
            fg=TEXT_MUTED, insertbackground=TEXT_DARK,
            width=24, bd=0
        )
        self._search_entry.pack(side="left", ipady=4)
        self._search_entry.insert(0, "Search products...")
        self._search_entry.bind("<FocusIn>",  self._on_search_focus_in)
        self._search_entry.bind("<FocusOut>", self._on_search_focus_out)

        # Clear button
        clear_btn = tk.Label(search_container, text="✕", bg=WHITE,
                             fg=TEXT_MUTED, font=(FONT_FAM, 10),
                             cursor="hand2")
        clear_btn.pack(side="left", padx=(2, 8))
        clear_btn.bind("<Button-1>", lambda _: self._clear_search())

        # Highlight border on focus
        search_container.bind("<FocusIn>", lambda _: search_container.config(highlightbackground=PRIMARY))
        self._search_entry.bind("<FocusIn>",
            lambda e: (self._on_search_focus_in(e),
                       search_container.config(highlightbackground=PRIMARY)))
        self._search_entry.bind("<FocusOut>",
            lambda e: (self._on_search_focus_out(e),
                       search_container.config(highlightbackground=BORDER)))

        # Scrollable grid
        outer = tk.Frame(panel, bg=BG)
        outer.pack(fill="both", expand=True)

        self.prod_canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=self.prod_canvas.yview)
        self.prod_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.prod_canvas.pack(side="left", fill="both", expand=True)

        self.prod_inner = tk.Frame(self.prod_canvas, bg=BG)
        self._prod_window = self.prod_canvas.create_window((0, 0), window=self.prod_inner, anchor="nw")

        self.prod_inner.bind("<Configure>",
                             lambda _: self.prod_canvas.configure(
                                 scrollregion=self.prod_canvas.bbox("all")))
        self.prod_canvas.bind("<Configure>",
                              lambda e: self.prod_canvas.itemconfig(self._prod_window, width=e.width))
        self.prod_canvas.bind("<Enter>",
                              lambda _: self.prod_canvas.bind_all("<MouseWheel>", self._on_scroll))
        self.prod_canvas.bind("<Leave>",
                              lambda _: self.prod_canvas.unbind_all("<MouseWheel>"))

    def _on_search_focus_in(self, e=None):
        if self.search_var.get() == "Search products...":
            self._search_entry.delete(0, "end")
            self._search_entry.config(fg=TEXT_DARK)

    def _on_search_focus_out(self, e=None):
        if not self.search_var.get():
            self._search_entry.insert(0, "Search products...")
            self._search_entry.config(fg=TEXT_MUTED)

    def _clear_search(self):
        self.search_var.set("")
        self._search_entry.config(fg=TEXT_MUTED)
        self._search_entry.insert(0, "Search products...")
        self._search_entry.config(fg=TEXT_MUTED)

    def _open_qty_dialog(self, prod):
        QuantityDialog(self.parent, prod, self.pos.cart_manager, self._img_cache, pos=self.pos)

    def _on_scroll(self, e):
        self.prod_canvas.yview_scroll(-1 * (e.delta // 120), "units")

    def _schedule_filter(self):
        if self._search_job:
            self.parent.after_cancel(self._search_job)
        self._search_job = self.parent.after(150, self._filter)

    def _filter(self):
        q = self.search_var.get().lower()
        if q in ("", "search products..."):
            self.display_products(self.pos.products)
        else:
            self.display_products([p for p in self.pos.products if q in p[1].lower()])

    def display_products(self, products):
        for w in self.prod_inner.winfo_children():
            w.destroy()
        self.prod_canvas.yview_moveto(0)
        self.prod_count_lbl.config(text=f"Products  ({len(products)} items)")

        COLS = 3
        IMG_W, IMG_H = 200, 160

        for idx, prod in enumerate(products):
            pid, name, price, *_ = prod
            row, col = divmod(idx, COLS)

            card = tk.Frame(self.prod_inner, bg=WHITE, cursor="hand2",
                            highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            self.prod_inner.grid_columnconfigure(col, weight=1, uniform="col")

            # Cover-fit image
            img_frame = tk.Frame(card, bg=BG, width=IMG_W, height=IMG_H)
            img_frame.pack(fill="x")
            img_frame.pack_propagate(False)

            photo = None
            if PIL_AVAILABLE:
                filename  = IMAGE_MAP.get(name, "no image.jpg")
                img_path  = os.path.join(ASSETS_DIR, filename)
                cache_key = (img_path, IMG_W, IMG_H)
                if cache_key not in self._img_cache:
                    try:
                        pil_img = Image.open(img_path).convert("RGB")
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
                tk.Label(img_frame, text="🍴", font=(FONT_FAM, 36),
                         bg=BG, fg=TEXT_MUTED).place(relx=0.5, rely=0.5, anchor="center")

            # Info strip
            info = tk.Frame(card, bg=WHITE, padx=10, pady=8)
            info.pack(fill="x")
            tk.Label(info, text=name, font=FONT_BOLD, fg=TEXT_DARK, bg=WHITE,
                     wraplength=160, justify="left", anchor="w").pack(fill="x")

            bottom = tk.Frame(info, bg=WHITE)
            bottom.pack(fill="x", pady=(4, 0))
            tk.Label(bottom, text=f"₱{price:,.2f}", font=(FONT_FAM, 13, "bold"),
                     fg=TEXT_DARK, bg=WHITE).pack(side="left")

            add_btn = tk.Label(bottom, text="+ Add", font=FONT_BOLD,
                               fg=WHITE, bg=PRIMARY, cursor="hand2", padx=10, pady=4)
            add_btn.pack(side="right")
            add_btn.bind("<Enter>", lambda e, b=add_btn: b.config(bg=TEXT_DARK))
            add_btn.bind("<Leave>", lambda e, b=add_btn: b.config(bg=PRIMARY))

            for widget in [card, img_frame] + list(img_frame.winfo_children()) + \
                          [info] + list(info.winfo_children()) + \
                          [bottom] + list(bottom.winfo_children()):
                widget.bind("<Button-1>", lambda _, p=prod: self._open_qty_dialog(p))
                widget.bind("<Enter>",    lambda _, c=card: c.config(highlightbackground=PRIMARY))
                widget.bind("<Leave>",    lambda _, c=card: c.config(highlightbackground=BORDER))
