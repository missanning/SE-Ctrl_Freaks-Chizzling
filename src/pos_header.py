import tkinter as tk
import os
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

BG      = "#FFF8EE"
WHITE   = "#FFFFFF"
HEADER  = "#E8820C"
BORDER  = "#FFD966"
FONT_FAM = "Segoe UI"
FONT_BOLD = (FONT_FAM, 12, "bold")
FONT_SMALL = (FONT_FAM, 10)


class POSHeader:
    def __init__(self, parent, username="cashier", role="cashier", logout_cmd=None):
        self.parent     = parent
        self.username   = username
        self.role       = role
        self.logout_cmd = logout_cmd
        self._logo_img  = None
        self.create_header()

    def create_header(self):
        bar = tk.Frame(self.parent, bg=HEADER, height=120)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "LOGO.png")
        logo_frame = tk.Frame(bar, bg=HEADER)
        logo_frame.pack(side="left", padx=(12, 4), pady=5)
        if PIL_AVAILABLE and os.path.exists(logo_path):
            img = Image.open(logo_path).resize((120, 120), Image.LANCZOS)
            self._logo_img = ImageTk.PhotoImage(img)
            tk.Label(logo_frame, image=self._logo_img, bg=HEADER).pack(side="left")
        tk.Label(logo_frame, text="Chizzling", font=(FONT_FAM, 18, "bold"),
                 fg=WHITE, bg=HEADER).pack(side="left", padx=(8, 0))
        tk.Label(logo_frame, text="POS.", font=(FONT_FAM, 18, "bold"),
                 fg=WHITE, bg=HEADER).pack(side="left")

        # Logout button
        logout_btn = tk.Label(bar, text="⏻  Logout", font=FONT_BOLD,
                              fg=WHITE, bg=HEADER, cursor="hand2", padx=14, pady=6)
        logout_btn.pack(side="right", padx=12, pady=14)
        logout_btn.bind("<Enter>", lambda e: logout_btn.config(bg="#C0620A"))
        logout_btn.bind("<Leave>", lambda e: logout_btn.config(bg=HEADER))
        logout_btn.bind("<Button-1>", lambda e: self._do_logout())

        # User pill
        pill = tk.Frame(bar, bg=HEADER, bd=0)
        pill.pack(side="right", padx=(0, 4), pady=10)
        initials = self.username[:2].upper()
        tk.Label(pill, text=initials, bg=WHITE, fg=HEADER,
                 font=FONT_BOLD, width=3, height=1).pack(side="left", padx=(6, 8), pady=4)
        info = tk.Frame(pill, bg=HEADER)
        info.pack(side="left", padx=(0, 6))
        tk.Label(info, text=self.username, font=FONT_BOLD,
                 fg=WHITE, bg=HEADER).pack(anchor="w")
        tk.Label(info, text=self.role.replace("_", " ").title(), font=FONT_SMALL,
                 fg=WHITE, bg=HEADER).pack(anchor="w")

        # Separator
        tk.Frame(self.parent, bg=BORDER, height=2).pack(fill="x")

    def _do_logout(self):
        if self.logout_cmd:
            self.logout_cmd()
        else:
            import sys
            sys.path.insert(0, os.path.dirname(__file__))
            self.parent.destroy()
            from LoginPage import MainApp
            new_root = tk.Tk()
            MainApp(new_root)
            new_root.mainloop()
