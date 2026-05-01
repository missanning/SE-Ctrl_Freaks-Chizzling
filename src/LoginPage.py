import tkinter as tk
from tkinter import messagebox
from database_setup import connect_db
import os
import sys
import platform

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

IS_MAC     = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

# ── Rounded rectangle ─────────────────────────────────────────────────────────
def _create_round_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
    points = [
        x1+radius, y1, x2-radius, y1, x2, y1,
        x2, y1+radius, x2, y2-radius, x2, y2,
        x2-radius, y2, x1+radius, y2, x1, y2,
        x1, y2-radius, x1, y1+radius, x1, y1,
    ]
    return self.create_polygon(points, smooth=not IS_MAC, **kwargs)

tk.Canvas.create_round_rectangle = _create_round_rectangle

# ── Theme ─────────────────────────────────────────────────────────────────────
BG           = "#ffffff"
CARD_BG      = "#ffffff"
ACCENT       = "#f5a623"
YELLOW       = "#ffd966"
BROWN        = "#7a3b10"
FG           = "#3b1f0a"
SUBTLE       = "#7a3b10"
ENTRY_BG     = "#fff8ee"
ENTRY_BORDER = "#f5a623"

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_FAM   = "Helvetica" if IS_MAC else ("Segoe UI" if IS_WINDOWS else "Sans Serif")
FONT_TITLE = (FONT_FAM, 13, "bold")
FONT_LABEL = (FONT_FAM, 11, "bold")
FONT_ENTRY = (FONT_FAM, 11)
FONT_BTN   = (FONT_FAM, 12, "bold")
FONT_SMALL = (FONT_FAM, 10)


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chizzling — Login")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        w, h = 400, 540
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        if IS_WINDOWS:
            self.root.overrideredirect(True)
            self.root.after(10, self._set_taskbar_presence)

        self._build_ui()

    def _build_ui(self):
        root = self.root

        # ── Top banner ──
        banner = tk.Frame(root, bg=BROWN, height=30)
        banner.pack(fill="x", side="top")
        banner.pack_propagate(False)
        tk.Label(banner, text="Chizzling POS", font=(FONT_FAM, 10, "bold"),
                 bg=BROWN, fg=YELLOW).pack(side="left", padx=10, pady=5)
        if IS_WINDOWS:
            tk.Button(banner, text="✕", font=(FONT_FAM, 10, "bold"),
                      bg=BROWN, fg=YELLOW, relief="flat", bd=0,
                      cursor="hand2", activebackground="#c0392b",
                      activeforeground="white",
                      command=root.destroy).pack(side="right", padx=8, pady=4)

        tk.Frame(root, bg=ACCENT, height=3).pack(fill="x", side="top")
        tk.Frame(root, bg=YELLOW, height=3).pack(fill="x", side="top")

        # ── Bottom strips ──
        tk.Frame(root, bg=BROWN,  height=6).pack(fill="x", side="bottom")
        tk.Frame(root, bg=ACCENT, height=3).pack(fill="x", side="bottom")
        tk.Frame(root, bg=YELLOW, height=3).pack(fill="x", side="bottom")

        # ── Center container ──
        center = tk.Frame(root, bg=BG)
        center.pack(fill="both", expand=True)

        card_border = tk.Frame(center, bg=BROWN, padx=2, pady=2)
        card_border.place(relx=0.5, rely=0.5, anchor="center")

        card = tk.Frame(card_border, bg=CARD_BG, padx=28, pady=22)
        card.pack()

        # ── Logo ──
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "LOGO.png")
        if PIL_AVAILABLE and os.path.exists(logo_path):
            img = Image.open(logo_path).resize((150, 150), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            tk.Label(card, image=self.logo_img, bg=CARD_BG).pack(pady=(0, 4))
        else:
            tk.Label(card, text="🛒", font=(FONT_FAM, 30),
                     bg=CARD_BG, fg=ACCENT).pack()

        tk.Label(card, text="POS and Inventory System",
                 font=FONT_TITLE, bg=CARD_BG, fg=BROWN).pack(pady=(2, 1))
        tk.Frame(card, bg=YELLOW, height=3, width=160).pack(pady=(0, 3))
        tk.Label(card, text="Sign in to your account",
                 font=FONT_SMALL, bg=CARD_BG, fg=SUBTLE).pack(pady=(0, 14))

        # ── Username ──
        tk.Label(card, text="Username", font=FONT_LABEL,
                 bg=CARD_BG, fg=BROWN, anchor="w").pack(fill="x")
        user_frame = tk.Frame(card, bg=ENTRY_BORDER, padx=1, pady=1)
        user_frame.pack(fill="x", pady=(3, 10))
        self.entry_username = tk.Entry(user_frame, font=FONT_ENTRY,
                                       bg=ENTRY_BG, fg=FG,
                                       insertbackground=FG, relief="flat", bd=0)
        self.entry_username.pack(fill="x", ipady=7, padx=5)
        self.entry_username.bind("<FocusIn>",  lambda e: user_frame.config(bg=ACCENT))
        self.entry_username.bind("<FocusOut>", lambda e: user_frame.config(bg=ENTRY_BORDER))
        self.entry_username.bind("<Key>", lambda e: self._clear_error())
        if IS_MAC:
            self.entry_username.bind("<Button-1>", lambda e: self.entry_username.focus_set())

        # ── Password ──
        tk.Label(card, text="Password", font=FONT_LABEL,
                 bg=CARD_BG, fg=BROWN, anchor="w").pack(fill="x")
        pw_border = tk.Frame(card, bg=ENTRY_BORDER, padx=1, pady=1)
        pw_border.pack(fill="x", pady=(3, 4))
        pw_frame = tk.Frame(pw_border, bg=ENTRY_BG)
        pw_frame.pack(fill="x")
        self.entry_password = tk.Entry(pw_frame, font=FONT_ENTRY,
                                       bg=ENTRY_BG, fg=FG,
                                       insertbackground=FG, relief="flat",
                                       bd=0, show="*")
        self.entry_password.pack(side=tk.LEFT, fill="x", expand=True,
                                 ipady=7, padx=(5, 0))
        self.entry_password.bind("<FocusIn>",  lambda e: pw_border.config(bg=ACCENT))
        self.entry_password.bind("<FocusOut>", lambda e: pw_border.config(bg=ENTRY_BORDER))
        self.entry_password.bind("<Key>", lambda e: self._clear_error())
        if IS_MAC:
            self.entry_password.bind("<Button-1>", lambda e: self.entry_password.focus_set())

        self.show_password = False
        tk.Button(pw_frame, text="👁", bg=ENTRY_BG, fg=SUBTLE,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._toggle_pw).pack(side=tk.RIGHT, padx=4)

        # ── Status ──
        self.display_label = tk.Label(card, text="", font=FONT_LABEL,
                                      bg="#FDECEA", fg="#C0392B",
                                      wraplength=320, justify="center",
                                      relief="flat", padx=8, pady=6)
        # don't pack yet — only shown when there's an error

        # ── Login button ──
        btn_w, btn_h = 280, 40
        btn_canvas = tk.Canvas(card, bg=CARD_BG, highlightthickness=0,
                               width=btn_w, height=btn_h)
        btn_canvas.pack(pady=(8, 0))

        self._btn_rect = btn_canvas.create_round_rectangle(
            2, 2, btn_w-2, btn_h-2, radius=20, fill=BROWN, outline=BROWN)
        self._btn_text = btn_canvas.create_text(
            btn_w//2, btn_h//2, text="Login", font=FONT_BTN, fill=YELLOW)

        for tag in (self._btn_rect, self._btn_text):
            btn_canvas.tag_bind(tag, "<Button-1>", lambda e: self.login())
            btn_canvas.tag_bind(tag, "<Enter>",
                                lambda e, c=btn_canvas: c.itemconfig(self._btn_rect, fill=ACCENT, outline=ACCENT))
            btn_canvas.tag_bind(tag, "<Leave>",
                                lambda e, c=btn_canvas: c.itemconfig(self._btn_rect, fill=BROWN, outline=BROWN))

        self.root.bind("<Return>", lambda e: self.login())

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _set_taskbar_presence(self):
        try:
            import ctypes
            hwnd  = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            style = (style & ~0x00000080) | 0x00040000
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
            self.root.withdraw()
            self.root.deiconify()
        except Exception:
            pass

    def _show_error(self, msg):
        self.display_label.config(text=f"⚠  {msg}")
        self.display_label.pack(fill="x", pady=(8, 0))

    def _clear_error(self):
        self.display_label.config(text="")
        self.display_label.pack_forget()
        self.entry_username.config(highlightthickness=0)
        self.entry_password.config(highlightthickness=0)

    def _toggle_pw(self):
        self.show_password = not self.show_password
        self.entry_password.config(show="" if self.show_password else "*")

    def _shake(self):
        x, y = self.root.winfo_x(), self.root.winfo_y()
        def step(i=0, moves=[10,-10,8,-8,5,-5,0]):
            if i < len(moves):
                self.root.geometry(f"+{x+moves[i]}+{y}")
                self.root.after(30, lambda: step(i+1))
        step()

    def _close_login(self):
        try:
            self.root.master.destroy()
        except Exception:
            self.root.destroy()

    # ── Auth ──────────────────────────────────────────────────────────────────
    def login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get()

        if not username or not password:
            self._show_error("Please enter username and password.")
            return

        con = connect_db()
        cur = con.cursor()
        cur.execute("SELECT role FROM users WHERE username=? AND password=?",
                    (username, password))
        result = cur.fetchone()
        con.close()

        if result is None:
            self._show_error("Invalid username or password.")
            self.entry_username.config(highlightbackground="#e74c3c",
                                       highlightcolor="#e74c3c", highlightthickness=2)
            self.entry_password.config(highlightbackground="#e74c3c",
                                       highlightcolor="#e74c3c", highlightthickness=2)
            self._shake()
            return

        role = result[0]
        actions = {
            "cashier":         self.open_chizzling_pos,
            "admin":           self.open_dashboard,
            "inventory_staff": self.open_inventory,
        }
        self._clear_error()
        messagebox.showinfo("Success", "Logged in successfully!")
        if role in actions:
            actions[role]()

    # ── Navigation ────────────────────────────────────────────────────────────
    def open_chizzling_pos(self):
        username = self.entry_username.get().strip()
        self._close_login()
        sys.path.insert(0, os.path.dirname(__file__))
        from ChizzlingPOS import ChizzlingPOS
        new_root = tk.Tk()
        ChizzlingPOS(new_root, username=username, role="cashier")
        new_root.mainloop()

    def open_dashboard(self):
        self._close_login()
        sys.path.insert(0, os.path.dirname(__file__))
        from dashboard import Dashboard
        new_root = tk.Tk()
        Dashboard(new_root)
        new_root.mainloop()

    def open_inventory(self):
        self._close_login()
        from ProductManagementSystem import ProductManagementSystem
        new_root = tk.Tk()
        ProductManagementSystem(new_root)
        new_root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    MainApp(root)
    root.mainloop()
