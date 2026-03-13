import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from database_setup import connect_db

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Main Window")
        self.root.geometry("300x300")

        self.label = tk.Label(root, text="Login Page")
        self.label.pack(pady=1)

        self.display_label = tk.Label(root, text="")
        self.display_label.pack(pady=10)

        self.label_username = tk.Label(root, text="Username:")
        self.label_username.pack(pady=5)

        self.entry_username = tk.Entry(root)
        self.entry_username.pack(pady=5)

        self.label_password = tk.Label(root, text="Password:")
        self.label_password.pack(pady=5)

        self.entry_password = tk.Entry(root)
        self.entry_password.pack(pady=5)

        self.login_button = tk.Button(root, text="Login", width=18, command=self.login)
        self.login_button.pack(pady=10)
    
    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        con = connect_db()
        cursor = con.cursor()
        cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        result = cursor.fetchone()
        con.close()

        if result is None:
            # Login failed
            self.display_label.config(text="Invalid username or password")
            messagebox.showerror("Error", "Invalid username or password")
            return

        # Login successful
        role = result[0]

        if role == "cashier":
            self.display_label.config(text="Logged in as Cashier")
            messagebox.showinfo("Success", "Logged in successfully!")
            self.open_chizzling_pos()

        elif role == "owner":
            self.display_label.config(text="Logged in as Owner")
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
        from ChizzlingPOS import POS
        new_root = tk.Tk()
        app = POS(new_root)
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
        self.root.destroy()

        new_root = tk.Tk()
        app = ProductManagementSystem(new_root)
        new_root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()