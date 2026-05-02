import tkinter as tk
from tkinter import ttk, messagebox
from database_setup import connect_db

ROLES    = ["admin", "cashier", "inventory_staff"]
BG       = "#FFF8EE"
SIDEBAR  = "#7a3b10"
ACCENT   = "#f5a623"
YELLOW   = "#ffd966"
FG_DARK  = "#3b1f0a"
FG_LIGHT = "#fff3e0"
CONTENT  = "#ffffff"
ROW_ALT  = "#fff3e0"
ENTRY_BG = "#fff8ee"
FONT     = "Segoe UI"


class UserManagement:
    def __init__(self, root, current_user_id: int = None):
        """
        :param current_user_id: ID of the logged-in user; prevents self-delete.
        """
        self.root            = root
        self.current_user_id = current_user_id
        self.selected_id     = None
        self._show_password  = False
        self._status_job     = None

        self.root.title("User Management — Chizzling POS")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.update_idletasks()
        w, h = 820, 660
        x = (self.root.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self._build_ui()
        self.load_users()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=SIDEBAR, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="👤  User Management",
                 font=(FONT, 14, "bold"), bg=SIDEBAR, fg=YELLOW
                 ).pack(side="left", padx=20, pady=10)
        tk.Frame(self.root, bg=ACCENT, height=3).pack(fill="x")
        tk.Frame(self.root, bg=YELLOW, height=2).pack(fill="x")

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        # ── Search bar ────────────────────────────────────────────────────────
        search_row = tk.Frame(body, bg=BG)
        search_row.pack(fill="x", pady=(0, 6))

        tk.Label(search_row, text="Registered Users",
                 font=(FONT, 13, "bold"), bg=BG, fg=SIDEBAR
                 ).pack(side="left")

        tk.Label(search_row, text="🔍", font=(FONT, 11),
                 bg=BG, fg=FG_DARK).pack(side="right", padx=(0, 4))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.load_users())
        tk.Entry(
            search_row, textvariable=self.search_var,
            font=(FONT, 11), bg=ENTRY_BG, fg=FG_DARK,
            relief="flat", highlightbackground=ACCENT,
            highlightthickness=1, width=22,
        ).pack(side="right", ipady=5)

        # ── Treeview ──────────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("UM.Treeview",
                        background=CONTENT, fieldbackground=CONTENT,
                        foreground=FG_DARK, font=(FONT, 11), rowheight=30)
        style.configure("UM.Treeview.Heading",
                        background=SIDEBAR, foreground=FG_LIGHT,
                        font=(FONT, 11, "bold"), relief="flat")
        style.map("UM.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", FG_DARK)])

        tree_frame = tk.Frame(body, bg=CONTENT)
        tree_frame.pack(fill="both", expand=True)

        cols = ("ID", "Username", "Role")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                 style="UM.Treeview", height=10)
        for col, w in (("ID", 60), ("Username", 320), ("Role", 200)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center" if col == "ID" else "w")
        self.tree.tag_configure("odd",  background=CONTENT)
        self.tree.tag_configure("even", background=ROW_ALT)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",         self._on_double_click)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        tk.Frame(body, bg=ACCENT, height=2).pack(fill="x", pady=(12, 16))

        # ── Form ──────────────────────────────────────────────────────────────
        tk.Label(body, text="User Details", font=(FONT, 13, "bold"),
                 bg=BG, fg=SIDEBAR).pack(anchor="w", pady=(0, 10))

        form = tk.Frame(body, bg=BG)
        form.pack(fill="x")

        tk.Label(form, text="Username", font=(FONT, 11, "bold"),
                 bg=BG, fg=FG_DARK).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
        self.entry_username = tk.Entry(
            form, font=(FONT, 11), bg=ENTRY_BG, fg=FG_DARK,
            relief="flat", highlightbackground=ACCENT,
            highlightthickness=1, width=24,
        )
        self.entry_username.grid(row=0, column=1, sticky="w", padx=(0, 24), pady=4, ipady=6)

        tk.Label(form, text="Password", font=(FONT, 11, "bold"),
                 bg=BG, fg=FG_DARK).grid(row=0, column=2, sticky="w", padx=(0, 10), pady=4)
        pw_frame = tk.Frame(form, bg=ENTRY_BG,
                            highlightbackground=ACCENT, highlightthickness=1)
        pw_frame.grid(row=0, column=3, sticky="w", padx=(0, 24), pady=4)
        self.entry_password = tk.Entry(
            pw_frame, font=(FONT, 11), bg=ENTRY_BG,
            fg=FG_DARK, relief="flat", show="*", width=20,
        )
        self.entry_password.pack(side="left", ipady=6, padx=(4, 0))
        tk.Button(pw_frame, text="👁", font=(FONT, 10), bg=ENTRY_BG, fg=FG_DARK,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._toggle_password).pack(side="left", padx=4)

        tk.Label(form, text="Role", font=(FONT, 11, "bold"),
                 bg=BG, fg=FG_DARK).grid(row=0, column=4, sticky="w", padx=(0, 10), pady=4)
        self.role_var = tk.StringVar(value=ROLES[0])
        ttk.Combobox(form, textvariable=self.role_var, values=ROLES,
                     width=16, state="readonly", font=(FONT, 11)
                     ).grid(row=0, column=5, sticky="w", pady=4, ipady=4)

        # Status label
        self.status_label = tk.Label(body, text="", font=(FONT, 10), bg=BG, fg=SIDEBAR)
        self.status_label.pack(anchor="w", pady=(8, 0))

        # Action buttons
        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(anchor="w", pady=(10, 0))

        for text, cmd, bg, fg in [
            ("➕  Add User",    self._add_user,    SIDEBAR,   FG_LIGHT),
            ("✏️  Update User", self._update_user, ACCENT,    FG_DARK),
            ("🗑  Delete User", self._delete_user, "#8b0000", FG_LIGHT),
            ("✕  Clear",       self._clear_form,  "#c0a080", FG_DARK),
        ]:
            tk.Button(btn_frame, text=text, command=cmd,
                      font=(FONT, 11, "bold"), bg=bg, fg=fg,
                      relief="flat", padx=16, pady=8,
                      activebackground=YELLOW, activeforeground=FG_DARK,
                      cursor="hand2").pack(side="left", padx=(0, 8))

        # Bottom strip
        tk.Frame(self.root, bg=ACCENT, height=3).pack(fill="x", side="bottom")
        tk.Frame(self.root, bg=SIDEBAR, height=8).pack(fill="x", side="bottom")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _toggle_password(self):
        self._show_password = not self._show_password
        self.entry_password.config(show="" if self._show_password else "*")

    def _set_status(self, msg: str, color: str = None, auto_clear: bool = True):
        if self._status_job:
            self.root.after_cancel(self._status_job)
            self._status_job = None
        self.status_label.config(text=msg, fg=color or SIDEBAR)
        if auto_clear and msg:
            self._status_job = self.root.after(4000, lambda: self._set_status(""))

    # ── Data ─────────────────────────────────────────────────────────────────

    def load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        query = self.search_var.get() if hasattr(self, "search_var") else ""
        con = connect_db()
        cur = con.cursor()
        if query.strip():
            cur.execute(
                "SELECT id, username, role FROM users WHERE username LIKE ? ORDER BY id",
                (f"%{query.strip()}%",),
            )
        else:
            cur.execute("SELECT id, username, role FROM users ORDER BY id")
        for i, row in enumerate(cur.fetchall()):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=row, tags=(tag,))
        con.close()

    # ── Tree events ───────────────────────────────────────────────────────────

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.selected_id = int(values[0])
        self.entry_username.delete(0, "end")
        self.entry_username.insert(0, values[1])
        self.entry_password.delete(0, "end")
        self.role_var.set(values[2])
        self._set_status(f"Selected user: {values[1]}", SIDEBAR, auto_clear=False)

    def _on_double_click(self, _=None):
        self._on_select()
        self.entry_username.focus_set()

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate(self, require_password: bool = True):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        role     = self.role_var.get()
        if not username:
            self._set_status("⚠  Username is required.", "#8b0000")
            return None
        if len(username) < 3:
            self._set_status("⚠  Username must be at least 3 characters.", "#8b0000")
            return None
        if require_password and not password:
            self._set_status("⚠  Password is required.", "#8b0000")
            return None
        if require_password and len(password) < 4:
            self._set_status("⚠  Password must be at least 4 characters.", "#8b0000")
            return None
        if not role:
            self._set_status("⚠  Role is required.", "#8b0000")
            return None
        return username, password, role

    # ── CRUD actions ─────────────────────────────────────────────────────────

    def _add_user(self):
        data = self._validate()
        if not data:
            return
        username, password, role = data
        if not messagebox.askyesno("Confirm", f"Add new user '{username}' as {role}?"):
            return
        try:
            con = connect_db()
            con.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role),
            )
            con.commit()
            con.close()
            self.load_users()
            self._clear_form()
            self._set_status(f"✔  User '{username}' created successfully.", "#2d6a2d")
        except Exception:
            self._set_status("⚠  Username already exists.", "#8b0000")

    def _update_user(self):
        if not self.selected_id:
            self._set_status("⚠  Select a user to update.", "#8b0000")
            return
        data = self._validate(require_password=False)
        if not data:
            return
        username, password, role = data

        # Duplicate-username check (allow keeping own username)
        con = connect_db()
        cur = con.cursor()
        cur.execute(
            "SELECT 1 FROM users WHERE username=? AND id!=?",
            (username, self.selected_id),
        )
        if cur.fetchone():
            con.close()
            self._set_status("⚠  That username is already taken.", "#8b0000")
            return
        con.close()

        if not messagebox.askyesno("Confirm", f"Update user '{username}'?"):
            return
        con = connect_db()
        if password:
            con.execute(
                "UPDATE users SET username=?, password=?, role=? WHERE id=?",
                (username, password, role, self.selected_id),
            )
        else:
            con.execute(
                "UPDATE users SET username=?, role=? WHERE id=?",
                (username, role, self.selected_id),
            )
        con.commit()
        con.close()
        self.load_users()
        self._clear_form()
        self._set_status(f"✔  User '{username}' updated successfully.", "#2d6a2d")

    def _delete_user(self):
        if not self.selected_id:
            self._set_status("⚠  Select a user to delete.", "#8b0000")
            return

        # Self-delete guard
        if self.current_user_id and self.selected_id == self.current_user_id:
            self._set_status("⚠  You cannot delete your own account.", "#8b0000")
            return

        # Use name from the tree, not the form field
        sel = self.tree.selection()
        username = self.tree.item(sel[0], "values")[1] if sel else "this user"

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{username}'?\nThis action cannot be undone.",
        ):
            return
        con = connect_db()
        con.execute("DELETE FROM users WHERE id=?", (self.selected_id,))
        con.commit()
        con.close()
        self.load_users()
        self._clear_form()
        self._set_status(f"✔  User '{username}' deleted.", "#2d6a2d")

    def _clear_form(self):
        self.selected_id = None
        self.entry_username.delete(0, "end")
        self.entry_password.delete(0, "end")
        self.role_var.set(ROLES[0])
        self.tree.selection_remove(self.tree.selection())
        self._set_status("", auto_clear=False)


if __name__ == "__main__":
    root = tk.Tk()
    # Pass the logged-in user's ID to enable the self-delete guard.
    # Example: UserManagement(root, current_user_id=1)
    UserManagement(root)
    root.mainloop()