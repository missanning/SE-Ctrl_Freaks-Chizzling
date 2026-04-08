import tkinter as tk
import os
import subprocess
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

def get_asset_path(filename):
    """Get the full path to an asset file"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_root, "assets", filename)

class POSHeader:
    def __init__(self, parent):
        self.parent = parent
        self.create_header()
    
    def logout_and_redirect(self):
        """Logout and redirect to login page"""
        try:
            # Close current window
            self.parent.destroy()
            # Launch login page
            subprocess.Popen(["python", "LoginPage.py"], 
                           cwd=os.path.dirname(__file__))
        except Exception as e:
            print(f"Error during logout: {e}")
    
    def create_header(self):
        # Shadow frame
        shadow = tk.Frame(self.parent, bg="#423e3e")
        shadow.grid(row=0, column=0, columnspan=3, sticky="ew", padx=3, pady=(3,0))

        # Actual header frame
        header = tk.Frame(self.parent)
        header.grid(row=0, column=0, columnspan=3, sticky="nsew")
        header.grid_propagate(False)

        # Load header image
        if Image is not None and ImageTk is not None:
            self.header_pil = Image.open(get_asset_path("HEADER.png"))
            self.header_img = ImageTk.PhotoImage(self.header_pil)

            header_label = tk.Label(header, image=self.header_img, borderwidth=0, relief="flat")
            header_label.pack(fill="x", expand=True)

            def _resize_header(event):
                if event.width <= 1 or event.height <= 1:
                    return
                resized = self.header_pil.resize((event.width, event.height), Image.LANCZOS)
                self.header_img = ImageTk.PhotoImage(resized)
                header_label.config(image=self.header_img)
                header_label.image = self.header_img

            header.bind("<Configure>", _resize_header)
        else:
            # Fall back to Tkinter PhotoImage
            self.header_img = tk.PhotoImage(file=get_asset_path("HEADER.png"))
            header_label = tk.Label(header, image=self.header_img, borderwidth=0, relief="solid")
            header_label.pack(fill="both", expand=True)
            
        # Logout button
        logout_btn = tk.Button(
            header_label,
            text="⎋ LOGOUT",
            command=self.logout_and_redirect,
            bg="#FF6600",
            fg="white",
            activebackground="#FF8844",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            width=10
        )
        logout_btn.place(relx=0.95, rely=0.5, anchor="e")