import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from database_setup import connect_db
import os
import sys
import platform
import math

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Extend Canvas to add rounded rectangle method
def create_round_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
    """Create a rounded rectangle on canvas"""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    # Mac doesn't handle smooth well, use regular polygon
    smooth = False if IS_MAC else True
    return self.create_polygon(points, **kwargs, smooth=smooth)

# Monkey patch the Canvas class
tk.Canvas.create_round_rectangle = create_round_rectangle

BG = "#ffffff"
CARD_BG = "#ffffff"
ACCENT = "#f5a623"       # orange
YELLOW = "#ffd966"       # yellow
BROWN = "#7a3b10"        # brown
FG = "#3b1f0a"
SUBTLE = "#7a3b10"
ENTRY_BG = "#fff8ee"
ENTRY_BORDER = "#f5a623"
# Detect platform for cross-platform compatibility
IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

# Cross-platform font selection
if IS_MAC:
    FONT_TITLE = ("Helvetica", 12, "bold")
    FONT_LABEL = ("Helvetica", 10, "bold")
    FONT_ENTRY = ("Helvetica", 11)
    FONT_BTN = ("Helvetica", 11, "bold")
elif IS_WINDOWS:
    FONT_TITLE = ("Segoe UI", 12, "bold")
    FONT_LABEL = ("Segoe UI", 10, "bold")
    FONT_ENTRY = ("Segoe UI", 11)
    FONT_BTN = ("Segoe UI", 11, "bold")
else:
    # Linux and other platforms
    FONT_TITLE = ("Sans Serif", 12, "bold")
    FONT_LABEL = ("Sans Serif", 10, "bold")
    FONT_ENTRY = ("Sans Serif", 11)
    FONT_BTN = ("Sans Serif", 11, "bold")

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chizzling — Login")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.update_idletasks()
        w, h = 420, 560
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        # Hide title bar but keep taskbar presence
        self.root.overrideredirect(True)
        self.root.after(10, lambda: self._set_taskbar_presence())

        # Top banner
        banner = tk.Frame(root, bg=BROWN, height=32)
        banner.pack(fill="x", side="top")
        banner.pack_propagate(False)
        tk.Label(banner, text="Chizzling POS", font=("Segoe UI", 10, "bold"), bg=BROWN, fg=YELLOW).pack(side="left", padx=10, pady=6)
        tk.Button(banner, text="✕", font=("Segoe UI", 10, "bold"), bg=BROWN, fg=YELLOW,
                  relief="flat", bd=0, cursor="hand2", activebackground="#c0392b",
                  activeforeground="white", command=self.root.destroy).pack(side="right", padx=8, pady=4)
        tk.Frame(root, bg=ACCENT, height=4).pack(fill="x", side="top")
        tk.Frame(root, bg=YELLOW, height=4).pack(fill="x", side="top")

        # Bottom strips
        tk.Frame(root, bg=BROWN, height=8).pack(fill="x", side="bottom")
        tk.Frame(root, bg=ACCENT, height=4).pack(fill="x", side="bottom")
        tk.Frame(root, bg=YELLOW, height=4).pack(fill="x", side="bottom")

        # Card frame with brown border effect
        card_border = tk.Frame(root, bg=BROWN, padx=2, pady=2)
        card_border.place(relx=0.5, rely=0.5, anchor="center", y=22)
        card = tk.Frame(card_border, bg=CARD_BG, padx=40, pady=40)
        card.pack()

        # Logo / Title
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "LOGO.png")
        if PIL_AVAILABLE and os.path.exists(logo_path):
            img = Image.open(logo_path).resize((140, 140), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            tk.Label(card, image=self.logo_img, bg=CARD_BG).pack(pady=(0, 6))
        else:
            # Cross-platform emoji fallback - use text cart icon for better compatibility
            fallback_font = ("Helvetica", 36) if IS_MAC else ("Segoe UI", 36)
            tk.Label(card, text="🛒", font=fallback_font, bg=CARD_BG, fg=ACCENT).pack()
        tk.Label(card, text="POS and Inventory System", font=FONT_TITLE, bg=CARD_BG, fg=BROWN).pack(pady=(3, 2))
        # Yellow underline accent
        tk.Frame(card, bg=YELLOW, height=3, width=160).pack(pady=(0, 4))
        tk.Label(card, text="Sign in to your account", font=FONT_LABEL, bg=CARD_BG, fg=SUBTLE).pack(pady=(0, 20))

        # Username
        tk.Label(card, text="Username", font=FONT_LABEL, bg=CARD_BG, fg=BROWN, anchor="w").pack(fill="x")
        user_frame = tk.Frame(card, bg=ENTRY_BORDER, padx=1, pady=1)
        user_frame.pack(fill="x", pady=(4, 14))
        self.entry_username = tk.Entry(user_frame, font=FONT_ENTRY, bg=ENTRY_BG, fg=FG,
                                       insertbackground=FG, relief="flat", bd=0)
        self.entry_username.pack(fill="x", ipady=8, padx=4)
        
        # Focus highlight for username - with Mac compatibility
        self.entry_username.bind("<FocusIn>", lambda e: self.on_focus_in(user_frame))
        self.entry_username.bind("<FocusOut>", lambda e: self.on_focus_out(user_frame))
        
        # Mac-specific: ensure entry is focusable
        if IS_MAC:
            self.entry_username.bind("<Button-1>", lambda e: self.entry_username.focus_set())
            self.entry_password.bind("<Button-1>", lambda e: self.entry_password.focus_set())

        # Password
        tk.Label(card, text="Password", font=FONT_LABEL, bg=CARD_BG, fg=BROWN, anchor="w").pack(fill="x")
        pw_border = tk.Frame(card, bg=ENTRY_BORDER, padx=1, pady=1)
        pw_border.pack(fill="x", pady=(4, 6))
        pw_frame = tk.Frame(pw_border, bg=ENTRY_BG)
        pw_frame.pack(fill="x")
        self.entry_password = tk.Entry(pw_frame, font=FONT_ENTRY, bg=ENTRY_BG, fg=FG,
                                        insertbackground=FG, relief="flat", bd=0, show="*")
        self.entry_password.pack(side=tk.LEFT, fill="x", expand=True, ipady=8, padx=(6, 0))
        # Focus highlight for password
        self.entry_password.bind("<FocusIn>", lambda e: self.on_focus_in(pw_border))
        self.entry_password.bind("<FocusOut>", lambda e: self.on_focus_out(pw_border))
        self.show_password = False
        self.toggle_button = tk.Button(pw_frame, text="👁", bg=ENTRY_BG, fg=SUBTLE,
                                        relief="flat", bd=0, cursor="hand2",
                                        command=self.toggle_password_visibility)
        self.toggle_button.pack(side=tk.RIGHT, padx=4)

        # Status label
        self.display_label = tk.Label(card, text="", font=FONT_LABEL, bg=CARD_BG, fg=ACCENT)
        self.display_label.pack(pady=(8, 0))

        # Login button with rounded corners using Canvas
        btn_canvas = tk.Canvas(card, bg=CARD_BG, highlightthickness=0, width=120, height=36)
        btn_canvas.pack(pady=(7, 0))
        
        # Draw rounded rectangle button
        radius = 20
        self.login_button_rect = btn_canvas.create_round_rectangle(
            0, 0, 120, 36,
            radius=radius, fill=BROWN, outline=BROWN
        )
        self.login_button_text = btn_canvas.create_text(
            60, 18,
            text="Login", font=FONT_BTN, fill=YELLOW
        )
        
        # Bind click events - Mac compatible
        button_click = "<Button-1>" if not IS_MAC else "<Button-1>"
        button_enter = "<Enter>"
        button_leave = "<Leave>"
        
        btn_canvas.tag_bind(self.login_button_rect, button_click, lambda e: self.login())
        btn_canvas.tag_bind(self.login_button_text, button_click, lambda e: self.login())
        btn_canvas.tag_bind(self.login_button_rect, button_enter, lambda e: self.on_button_hover(btn_canvas, True))
        btn_canvas.tag_bind(self.login_button_text, button_enter, lambda e: self.on_button_hover(btn_canvas, True))
        btn_canvas.tag_bind(self.login_button_rect, button_leave, lambda e: self.on_button_hover(btn_canvas, False))
        btn_canvas.tag_bind(self.login_button_text, button_leave, lambda e: self.on_button_hover(btn_canvas, False))
        
        # Store reference for hover effect
        self.btn_canvas = btn_canvas
        
        # Return key binding - cross-platform
        return_key = "<Return>" if not IS_MAC else "<Return>"
        self.root.bind(return_key, lambda e: self.login())
    
    def _set_taskbar_presence(self):
        """Restore taskbar button after hiding title bar on Windows."""
        try:
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            self.root.withdraw()
            self.root.deiconify()
        except Exception:
            pass

    def _quit(self):
        self.root.destroy()
        try:
            self.root.master.destroy()
        except Exception:
            pass

    def on_button_hover(self, canvas, hover):
        """Handle button hover effect"""
        if hover:
            canvas.itemconfig(self.login_button_rect, fill=ACCENT, outline=ACCENT)
        else:
            canvas.itemconfig(self.login_button_rect, fill=BROWN, outline=BROWN)

    def on_focus_in(self, frame):
        """Handle focus in event - highlight border"""
        frame.config(bg=ACCENT)

    def on_focus_out(self, frame):
        """Handle focus out event - reset border"""
        frame.config(bg=ENTRY_BORDER)

    def shake_window(self):
        """Shake animation for error feedback"""
        x = self.root.winfo_x()
        original_x = x
        # Shake pattern: left, right, left, right, center
        for i in range(6):
            if i % 2 == 0:
                self.root.geometry(f"+{original_x + 10}+{self.root.winfo_y()}")
            else:
                self.root.geometry(f"+{original_x - 10}+{self.root.winfo_y()}")
            self.root.update()
            self.root.after(30)
        # Return to center
        self.root.geometry(f"+{original_x}+{self.root.winfo_y()}")
    
    def toggle_password_visibility(self):
        if self.show_password:
            self.entry_password.config(show="*")
            self.show_password = False
        else:
            self.entry_password.config(show="")
            self.show_password = True
    
    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        if not username or not password:
            self.display_label.config(text="Please input a valid username and password")
            messagebox.showerror("Error", "Please input a valid username and password")
            return

        con = connect_db()
        cursor = con.cursor()
        cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        result = cursor.fetchone()
        con.close()

        if result is None:
            # Login failed - shake animation and highlight fields
            self.display_label.config(text="Invalid username or password")
            self.entry_username.config(highlightbackground="#e74c3c", highlightcolor="#e74c3c", highlightthickness=2)
            self.entry_password.config(highlightbackground="#e74c3c", highlightcolor="#e74c3c", highlightthickness=2)
            self.shake_window()
            return

        # Login successful
        role = result[0]

        if role == "cashier":
            self.display_label.config(text="Logged in as Cashier")
            messagebox.showinfo("Success", "Logged in successfully!")
            self.open_chizzling_pos()

        elif role == "admin":
            self.display_label.config(text="Logged in as Admin")
            messagebox.showinfo("Success", "Logged in successfully!")
            self.open_dashboard()

        elif role == "inventory_staff":
            self.display_label.config(text="Logged in as Inventory Staff")
            messagebox.showinfo("Success", "Logged in successfully!")
            self.LoginInventoryStaff()

        else:
            self.display_label.config(text=f"Logged in as {role}")
            messagebox.showinfo("Success", f"Logged in as {role}")

    def _close_login(self):
        try:
            self.root.master.destroy()
        except Exception:
            self.root.destroy()

    def open_chizzling_pos(self):
        self._close_login()
        import sys, os
        sys.path.insert(0, os.path.dirname(__file__))
        from ChizzlingPOS import ChizzlingPOS
        new_root = tk.Tk()
        ChizzlingPOS(new_root)
        new_root.mainloop()

    def open_dashboard(self):
        self._close_login()
        import sys, os
        sys.path.insert(0, os.path.dirname(__file__))
        from dashboard import Dashboard
        new_root = tk.Tk()
        Dashboard(new_root)
        new_root.mainloop()

    def LoginInventoryStaff(self):
        from ProductManagementSystem import ProductManagementSystem
        self._close_login()
        new_root = tk.Tk()
        ProductManagementSystem(new_root)
        new_root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()