import tkinter as tk
from tkinter import messagebox
import database

# Create table when program starts
database.create_table()

# Main window
root = tk.Tk()
root.title("Simple Login System")
root.geometry("300x250")

# Functions
def register():
    username = entry_username.get()
    password = entry_password.get()

    if username == "" or password == "":
        messagebox.showwarning("Error", "All fields are required!")
        return

    if database.register_user(username, password):
        messagebox.showinfo("Success", "User registered successfully!")
    else:
        messagebox.showerror("Error", "Username already exists!")

def login():
    username = entry_username.get()
    password = entry_password.get()

    if database.login_user(username, password):
        messagebox.showinfo("Success", "Login successful!")
    else:
        messagebox.showerror("Error", "Invalid username or password")

# UI Components
tk.Label(root, text="Login System", font=("Arial", 14)).pack(pady=10)

tk.Label(root, text="Username").pack()
entry_username = tk.Entry(root)
entry_username.pack()

tk.Label(root, text="Password").pack()
entry_password = tk.Entry(root, show="*")
entry_password.pack()

tk.Button(root, text="Register", width=10, command=register).pack(pady=5)
tk.Button(root, text="Login", width=10, command=login).pack()

root.mainloop()