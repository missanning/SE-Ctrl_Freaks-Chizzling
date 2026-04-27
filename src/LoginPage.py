import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from database_setup import connect_db
import os
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
    return self.create_polygon(points, **kwargs, smooth=True)

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
FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_ENTRY = ("Segoe UI", 11)
FONT_BTN = ("Segoe UI", 11, "bold")

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chizzling — Login")
        self.root.overrideredirect(True)
        self.root.configure(bg=BG)
        self.root.update_idletasks()
        w, h = 420, 500
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Top banner strip with close button
        banner = tk.Frame(root, bg=BROWN, height=28)
        banner.pack(fill="x", side="top")
        banner.pack_propagate(False)
        tk.Button(banner, text="X", font=("Segoe UI", 10, "bold"), bg=BROWN, fg=YELLOW,
                  relief="flat", bd=0, cursor="hand2", activebackground="#c0392b",
                  activeforeground="#ffffff", command=root.destroy).pack(side="right", padx=6, pady=4)
        accent_strip = tk.Frame(root, bg=ACCENT, height=4)
        accent_strip.pack(fill="x", side="top")
        yellow_strip = tk.Frame(root, bg=YELLOW, height=4)
        yellow_strip.pack(fill="x", side="top")

        # Bottom banner strip
        bottom_yellow = tk.Frame(root, bg=YELLOW, height=4)
        bottom_yellow.pack(fill="x", side="bottom")
        bottom_accent = tk.Frame(root, bg=ACCENT, height=4)
        bottom_accent.pack(fill="x", side="bottom")
        bottom_brown = tk.Frame(root, bg=BROWN, height=8)
        bottom_brown.pack(fill="x", side="bottom")

        # Card frame with brown border effect
        card_border = tk.Frame(root, bg=BROWN, padx=2, pady=2)
        card_border.place(relx=0.5, rely=0.5, anchor="center")
        card = tk.Frame(card_border, bg=CARD_BG, padx=40, pady=40)
        card.pack()

        # Logo / Title
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "LOGO.png")
        if PIL_AVAILABLE and os.path.exists(logo_path):
            img = Image.open(logo_path).resize((140, 140), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            tk.Label(card, image=self.logo_img, bg=CARD_BG).pack(pady=(0, 6))
        else:
            tk.Label(card, text="🛒", font=("Segoe UI", 36), bg=CARD_BG, fg=ACCENT).pack()
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
        # Focus highlight for username
        self.entry_username.bind("<FocusIn>", lambda e: self.on_focus_in(user_frame))
        self.entry_username.bind("<FocusOut>", lambda e: self.on_focus_out(user_frame))

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
        
        # Bind click events
        btn_canvas.tag_bind(self.login_button_rect, "<Button-1>", lambda e: self.login())
        btn_canvas.tag_bind(self.login_button_text, "<Button-1>", lambda e: self.login())
        btn_canvas.tag_bind(self.login_button_rect, "<Enter>", lambda e: self.on_button_hover(btn_canvas, True))
        btn_canvas.tag_bind(self.login_button_text, "<Enter>", lambda e: self.on_button_hover(btn_canvas, True))
        btn_canvas.tag_bind(self.login_button_rect, "<Leave>", lambda e: self.on_button_hover(btn_canvas, False))
        btn_canvas.tag_bind(self.login_button_text, "<Leave>", lambda e: self.on_button_hover(btn_canvas, False))
        
        # Store reference for hover effect
        self.btn_canvas = btn_canvas
        
        self.root.bind("<Return>", lambda e: self.login())
    
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

    def open_chizzling_pos(self):
        self.root.destroy()
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from ChizzlingPOS import ChizzlingPOS
        new_root = tk.Tk()
        app = ChizzlingPOS(new_root)
        new_root.mainloop()

    def open_dashboard(self):
        self.root.destroy()
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from dashboard import Dashboard
        new_root = tk.Tk()
        app = Dashboard(new_root)
        new_root.mainloop()

    def LoginInventoryStaff(self):
        from ProductManagementSystem import ProductManagementSystem
        self.root.destroy()

        new_root = tk.Tk()
        app = ProductManagementSystem(new_root)
        new_root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()