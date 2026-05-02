import tkinter as tk
from tkinter import ttk, messagebox
from database_setup import connect_db

ROLES = ["admin", "cashier", "inventory_staff"]


class UserManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("User Management")
        self.root.geometry("700x500")
        self.root.configure(bg="#FAF3E1")
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"700x500+{(sw-700)//2}+{(sh-500)//2}")
        self._build_ui()
        self.load_users()

    def _build_ui(self):
        # Header
        tk.Label(self.root, text="User Management", font=("Arial", 16, "bold"),
                 bg="#FF6600", fg="white").pack(fill="x", pady=(0, 10))

        # Table
        cols = ("ID", "Username", "Role")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", height=12)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80 if col == "ID" else 250)
        self.tree.pack(fill="both", expand=True, padx=20)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Form
        form = tk.Frame(self.root, bg="#FAF3E1")
        form.pack(pady=10)

        tk.Label(form, text="Username:", bg="#FAF3E1").grid(row=0, column=0, padx=5)
        self.entry_username = tk.Entry(form, width=20)
        self.entry_username.grid(row=0, column=1, padx=5)

        tk.Label(form, text="Password:", bg="#FAF3E1").grid(row=0, column=2, padx=5)
        self.entry_password = tk.Entry(form, width=20, show="*")
        self.entry_password.grid(row=0, column=3, padx=5)

        tk.Label(form, text="Role:", bg="#FAF3E1").grid(row=0, column=4, padx=5)
        self.role_var = tk.StringVar(value=ROLES[0])
        ttk.Combobox(form, textvariable=self.role_var, values=ROLES,
                     width=14, state="readonly").grid(row=0, column=5, padx=5)

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#FAF3E1")
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Add User", bg="#28A745", fg="white",
                  command=self.add_user).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Update User", bg="#007BFF", fg="white",
                  command=self.update_user).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete User", bg="#DC3545", fg="white",
                  command=self.delete_user).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Clear", bg="#6C757D", fg="white",
                  command=self.clear_form).pack(side="left", padx=5)

        self.selected_id = None

    def load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        con = connect_db()
        cursor = con.cursor()
        cursor.execute("SELECT id, username, role FROM users ORDER BY id")
        for row in cursor.fetchall():
            self.tree.insert("", "end", values=row)
        con.close()

    def on_select(self, _):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_id = values[0]
        self.entry_username.delete(0, "end")
        self.entry_username.insert(0, values[1])
        self.entry_password.delete(0, "end")
        self.role_var.set(values[2])

    def _validate(self, require_password=True):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        role = self.role_var.get()
        if not username:
            messagebox.showerror("Error", "Username is required.")
            return None
        if require_password and not password:
            messagebox.showerror("Error", "Password is required.")
            return None
        if not role:
            messagebox.showerror("Error", "Role is required.")
            return None
        return username, password, role

    def add_user(self):
        data = self._validate()
        if not data:
            return
        username, password, role = data
        try:
            con = connect_db()
            con.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                        (username, password, role))
            con.commit()
            con.close()
            self.load_users()
            self.clear_form()
            messagebox.showinfo("Success", f"User '{username}' created.")
        except Exception as e:
            messagebox.showerror("Error", f"Username already exists.\n{e}")

    def update_user(self):
        if not self.selected_id:
            messagebox.showerror("Error", "Select a user to update.")
            return
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        role = self.role_var.get()
        if not username or not role:
            messagebox.showerror("Error", "Username and role are required.")
            return
        con = connect_db()
        if password:
            con.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?",
                        (username, password, role, self.selected_id))
        else:
            con.execute("UPDATE users SET username=?, role=? WHERE id=?",
                        (username, role, self.selected_id))
        con.commit()
        con.close()
        self.load_users()
        self.clear_form()
        messagebox.showinfo("Success", "User updated.")

    def delete_user(self):
        if not self.selected_id:
            messagebox.showerror("Error", "Select a user to delete.")
            return
        username = self.entry_username.get().strip()
        if not messagebox.askyesno("Confirm", f"Delete user '{username}'?"):
            return
        con = connect_db()
        con.execute("DELETE FROM users WHERE id=?", (self.selected_id,))
        con.commit()
        con.close()
        self.load_users()
        self.clear_form()
        messagebox.showinfo("Success", "User deleted.")

    def clear_form(self):
        self.selected_id = None
        self.entry_username.delete(0, "end")
        self.entry_password.delete(0, "end")
        self.role_var.set(ROLES[0])
        self.tree.selection_remove(self.tree.selection())


if __name__ == "__main__":
    root = tk.Tk()
    UserManagement(root)
    root.mainloop()
