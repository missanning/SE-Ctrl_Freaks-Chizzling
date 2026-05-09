import tkinter as tk
import platform

WHITE      = "#FFFFFF"
PRIMARY    = "#F5A623"
PRIMARY_LT = "#FFF0D0"
TEXT_DARK  = "#3B1F0A"
BORDER     = "#FFD966"

_SYS     = platform.system()
FONT_FAM = "Helvetica" if _SYS == "Darwin" else ("Segoe UI" if _SYS == "Windows" else "Sans Serif")
FONT_BOLD = (FONT_FAM, 12, "bold")

ICONS = {
    "all": "     🍽️", "meals": "🍱", "snacks": "🍿",
    "drinks": "🥤", "alcohol": "🍺",
    "pizza": "🍕", "burger": "🍔", "salad": "🥗",
    "dessert": "🍨", "combo": "🍱",
}


class CategoryNavigation:
    def __init__(self, parent, pos_instance):
        self.parent     = parent
        self.pos        = pos_instance
        self.active_cat = "All"
        self._chips     = {}   # cat -> {"chip", "icon", "text"}
        self._create_sidebar()

    def _create_sidebar(self):
        sidebar = tk.Frame(self.parent, bg=WHITE)
        sidebar.pack(fill="both", expand=True)

        tk.Label(sidebar, text="Category", font=FONT_BOLD,
                 fg=TEXT_DARK, bg=WHITE).pack(pady=(14, 8))
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=8)

        self.cat_frame = tk.Frame(sidebar, bg=WHITE)
        self.cat_frame.pack(fill="both", expand=True, pady=4)

    def load_categories(self, cats):
        for w in self.cat_frame.winfo_children():
            w.destroy()
        self._chips = {}
        for cat in cats:
            self._make_chip(cat)

    def _make_chip(self, cat):
        is_active = (cat.lower() == self.active_cat.lower())
        chip_bg   = PRIMARY if is_active else WHITE
        fg        = WHITE   if is_active else TEXT_DARK
        icon      = ICONS.get(cat.lower(), "🍴")

        chip = tk.Frame(self.cat_frame, bg=chip_bg, cursor="hand2")
        chip.pack(fill="x", padx=8, pady=2)

        icon_lbl = tk.Label(chip, text=icon, font=(FONT_FAM, 22),
                            bg=chip_bg, anchor="center")
        icon_lbl.pack(fill="x", pady=(8, 2))

        text_lbl = tk.Label(chip, text=cat,
                            font=(FONT_FAM, 11, "bold" if is_active else "normal"),
                            fg=fg, bg=chip_bg, anchor="center")
        text_lbl.pack(fill="x", pady=(0, 8))

        self._chips[cat] = {"chip": chip, "icon": icon_lbl, "text": text_lbl}

        for w in (chip, icon_lbl, text_lbl):
            w.bind("<Button-1>", lambda _, c=cat: self.set_active_category(c))
            w.bind("<Enter>",    lambda _, c=cat: self._on_hover(c, True))
            w.bind("<Leave>",    lambda _, c=cat: self._on_hover(c, False))

    def _on_hover(self, cat, entering):
        if cat.lower() == self.active_cat.lower():
            return
        w = self._chips[cat]
        bg = PRIMARY_LT if entering else WHITE
        w["chip"].config(bg=bg)
        w["icon"].config(bg=bg)
        w["text"].config(bg=bg)

    def set_active_category(self, category):
        self.active_cat = category
        for cat, w in self._chips.items():
            is_active = (cat.lower() == category.lower())
            chip_bg   = PRIMARY if is_active else WHITE
            fg        = WHITE   if is_active else TEXT_DARK
            w["chip"].config(bg=chip_bg)
            w["icon"].config(bg=chip_bg)
            w["text"].config(bg=chip_bg, fg=fg,
                             font=(FONT_FAM, 11, "bold" if is_active else "normal"))

        if category.lower() == "all":
            self.pos.load_products(None)
        else:
            self.pos.load_products(category)
