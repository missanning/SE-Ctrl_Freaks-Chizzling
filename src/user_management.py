import tkinter as tk
from tkinter import ttk, messagebox
from database_setup import connect_db
from security import hash_password

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


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, bg, fg, hover_bg,
                 font=None, padx=16, pady=8, radius=14, **kwargs):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, **kwargs)
        self._bg       = bg
        self._hover_bg = hover_bg
        self._fg       = fg
        self._text     = text
        self._command  = command
        self._font     = font or (FONT, 11, "bold")
        self._padx     = padx
        self._pady     = pady
        self._radius   = radius
        self._draw(bg)
        self.bind("<Enter>",    lambda _: self._draw(self._hover_bg))
        self.bind("<Leave>",    lambda _: self._draw(self._bg))
        self.bind("<Button-1>", lambda _: command())
        self.config(cursor="hand2")

    def _draw(self, bg):
        self.delete("all")
        # measure text
        tmp = tk.Label(self, text=self._text, font=self._font)
        tmp.update_idletasks()
        tw = tmp.winfo_reqwidth()
        th = tmp.winfo_reqheight()
        tmp.destroy()
        w = tw + self._padx * 2
        h = th + self._pady * 2
        self.config(width=w, height=h)
        r = self._radius
        self.create_arc(0,     0,     r*2, r*2, start=90,  extent=90,  fill=bg, outline=bg)
        self.create_arc(w-r*2, 0,     w,   r*2, start=0,   extent=90,  fill=bg, outline=bg)
        self.create_arc(0,     h-r*2, r*2, h,   start=180, extent=90,  fill=bg, outline=bg)
        self.create_arc(w-r*2, h-r*2, w,   h,   start=270, extent=90,  fill=bg, outline=bg)
        self.create_rectangle(r, 0, w-r, h, fill=bg, outline=bg)
        self.create_rectangle(0, r, w, h-r, fill=bg, outline=bg)
        self.create_text(w//2, h//2, text=self._text, fill=self._fg,
                         font=self._font)

    def config_btn(self, text=None, bg=None, fg=None, hover_bg=None):
        if text:     self._text     = text
        if bg:       self._bg       = bg
        if fg:       self._fg       = fg
        if hover_bg: self._hover_bg = hover_bg
        self._draw(self._bg)

class UserManagement:
    def __init__(self, root, current_user_id: int = None, on_close=None):
        """
        :param current_user_id: ID of the logged-in user; prevents self-delete.
        :param on_close: optional callback invoked after update to return to parent.
        """
        self.root            = root
        self.current_user_id = current_user_id
        self.on_close        = on_close
        self.selected_id     = None
        self._show_password  = False
        self._status_job     = None
        self._edit_mode      = False
        self.current_tab     = "active"  # Track current tab

        self.root.title("User Management — Chizzling POS")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.update_idletasks()
        w, h = 920, 650
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
        body.pack(fill="both", expand=True, padx=20, pady=10)

        # ── Tabs ──────────────────────────────────────────────────────────────
        tabs_frame = tk.Frame(body, bg=BG)
        tabs_frame.pack(fill="x", pady=(0, 8))

        self.active_tab_btn = RoundedButton(
            tabs_frame, text="Active Users", command=lambda: self._switch_tab("active"),
            bg=SIDEBAR, fg=FG_LIGHT, hover_bg="#9b5b30",
            font=(FONT, 11, "bold"), padx=14, pady=7
        )
        self.active_tab_btn.pack(side="left", padx=(0, 8))

        self.deleted_tab_btn = RoundedButton(
            tabs_frame, text="Deleted Users", command=lambda: self._switch_tab("deleted"),
            bg="#c0a080", fg=FG_DARK, hover_bg="#d4b896",
            font=(FONT, 11, "bold"), padx=14, pady=7
        )
        self.deleted_tab_btn.pack(side="left")

        # ── Search bar ────────────────────────────────────────────────────────
        search_row = tk.Frame(body, bg=BG)
        search_row.pack(fill="x", pady=(8, 8))

        self.tab_label = tk.Label(search_row, text="Active Users",
                 font=(FONT, 13, "bold"), bg=BG, fg=SIDEBAR)
        self.tab_label.pack(side="left")

        # Minimal search container
        search_pill = tk.Frame(search_row, bg=CONTENT, highlightbackground="#ddd", highlightthickness=1)
        search_pill.pack(side="right")

        tk.Label(search_pill, text="🔍", font=(FONT, 10), bg=CONTENT, fg="#999"
                 ).pack(side="left", padx=(8, 4), pady=6)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.load_users())
        tk.Entry(
            search_pill, textvariable=self.search_var,
            font=(FONT, 10), bg=CONTENT, fg=FG_DARK,
            relief="flat", bd=0, width=20, insertbackground=SIDEBAR,
        ).pack(side="left", ipady=4, padx=(0, 8))

        # ── Treeview ──────────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("UM.Treeview",
                        background=CONTENT, fieldbackground=CONTENT,
                        foreground=FG_DARK, font=(FONT, 11), rowheight=30)
        style.configure("UM.Treeview.Heading",
                        background=SIDEBAR, foreground=FG_LIGHT,
                        font=(FONT, 11, "bold"), relief="flat")
        style.map("UM.Treeview.Heading",
                  background=[("active", SIDEBAR), ("pressed", SIDEBAR)],
                  foreground=[("active", FG_LIGHT), ("pressed", FG_LIGHT)])
        style.map("UM.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", FG_DARK)])

        tree_frame = tk.Frame(body, bg=CONTENT)
        tree_frame.pack(fill="both", expand=False)

        cols = ("ID", "Username", "Role")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                 style="UM.Treeview", height=5)
        for col, w in (("ID", 80), ("Username", 400), ("Role", 200)):
            self.tree.heading(col, text=col, command=lambda: None)
            self.tree.column(col, width=w, anchor="center" if col == "ID" else "w")
        self.tree.tag_configure("odd",  background=CONTENT)
        self.tree.tag_configure("even", background=ROW_ALT)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",         self._on_double_click)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        tk.Frame(body, bg=ACCENT, height=2).pack(fill="x", pady=(6, 8))

        # ── Form ──────────────────────────────────────────────────────────────
        details_row = tk.Frame(body, bg=BG)
        details_row.pack(fill="x", pady=(0, 4))
        tk.Label(details_row, text="User Details", font=(FONT, 12, "bold"),
                 bg=BG, fg=SIDEBAR).pack(side="left")
        
        # Instructions label
        self.instruction_label = tk.Label(
            details_row, text="← Select a user to edit, or fill the form to add new user",
            font=(FONT, 10), bg=BG, fg="#999", anchor="w"
        )
        self.instruction_label.pack(side="left", padx=(10, 0))

        # Form card - always visible
        self.form_card = tk.Frame(body, bg=CONTENT,
                                  highlightbackground="#e0d0c0", highlightthickness=1)
        self.form_card.pack(fill="x", pady=(0, 8))

        self.form = tk.Frame(self.form_card, bg=CONTENT)
        self.form.pack(fill="x", padx=16, pady=10)

        # Row 0 — Username & Password
        self.lbl_username = tk.Label(self.form, text="Username", font=(FONT, 10, "bold"),
                                     bg=CONTENT, fg=FG_DARK)
        self.lbl_username.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 4))
        
        self.entry_username = tk.Entry(
            self.form, font=(FONT, 11), bg=ENTRY_BG, fg=FG_DARK,
            relief="flat", highlightbackground=ACCENT, highlightthickness=1, width=22,
        )
        self.entry_username.grid(row=1, column=0, sticky="ew", padx=(0, 20), pady=(0, 6), ipady=5)
        
        self.lbl_password = tk.Label(self.form, text="Password (leave blank to keep current)", 
                                     font=(FONT, 10, "bold"), bg=CONTENT, fg=FG_DARK)
        self.lbl_password.grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(0, 4))
        
        pw_frame = tk.Frame(self.form, bg=ENTRY_BG,
                            highlightbackground=ACCENT, highlightthickness=1)
        pw_frame.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=(0, 6))
        
        self.entry_password = tk.Entry(
            pw_frame, font=(FONT, 11), bg=ENTRY_BG,
            fg=FG_DARK, relief="flat", show="*", width=18,
        )
        self.entry_password.pack(side="left", fill="x", expand=True, ipady=5, padx=(6, 0))
        tk.Button(pw_frame, text="👁️", font=(FONT, 10), bg=ENTRY_BG, fg=FG_DARK,
                  relief="flat", bd=0, cursor="hand2",
                  activebackground=ENTRY_BG, activeforeground=FG_DARK,
                  command=self._toggle_password).pack(side="right", padx=(0, 6))
        self.pw_frame = pw_frame

        # Row 1 — Role
        self.lbl_role = tk.Label(self.form, text="Role", font=(FONT, 10, "bold"),
                                 bg=CONTENT, fg=FG_DARK)
        self.lbl_role.grid(row=0, column=2, sticky="w", padx=(0, 8), pady=(0, 4))
        
        self.role_var = tk.StringVar(value="")
        self.combo_role = ttk.Combobox(self.form, textvariable=self.role_var, values=ROLES,
                                       width=20, state="readonly", font=(FONT, 11))
        self.combo_role.grid(row=1, column=2, sticky="w", pady=(0, 6), ipady=4)
        self.combo_role.set("")  # Set to blank initially

        # Status label
        self.status_label = tk.Label(body, text="", font=(FONT, 10), bg=BG, fg=SIDEBAR)
        self.status_label.pack(anchor="w", pady=(2, 4))

        # Action buttons
        self.btn_frame = tk.Frame(body, bg=BG)
        self.btn_frame.pack(anchor="w", pady=(2, 10))

        # Active users buttons
        self.active_btns = tk.Frame(self.btn_frame, bg=BG)
        self.active_btns.pack()
        for text, cmd, bg, fg, hover in [
            ("➕  Add User",    self._add_user,    SIDEBAR,   FG_LIGHT, "#9b5b30"),
            ("✏️  Update User", self._update_user, ACCENT,    FG_DARK,  YELLOW),
            ("🗑  Delete User", self._delete_user, "#8b0000", FG_LIGHT, "#a00000"),
            ("✕  Clear",       self._clear_form,  "#c0a080", FG_DARK,  "#d4b896"),
        ]:
            RoundedButton(self.active_btns, text=text, command=cmd,
                          bg=bg, fg=fg, hover_bg=hover,
                          font=(FONT, 10, "bold"), padx=14, pady=7
                          ).pack(side="left", padx=(0, 8))

        # Deleted users buttons
        self.deleted_btns = tk.Frame(self.btn_frame, bg=BG)
        for text, cmd, bg, fg, hover in [
            ("♻️  Restore User", self._restore_user, "#2d6a2d", FG_LIGHT, "#3d7a3d"),
            ("🗑  Permanently Delete", self._permanent_delete, "#8b0000", FG_LIGHT, "#a00000"),
            ("✕  Clear",       self._clear_form,  "#c0a080", FG_DARK,  "#d4b896"),
        ]:
            RoundedButton(self.deleted_btns, text=text, command=cmd,
                          bg=bg, fg=fg, hover_bg=hover,
                          font=(FONT, 10, "bold"), padx=14, pady=7
                          ).pack(side="left", padx=(0, 8))

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

    def _switch_tab(self, tab):
        self.current_tab = tab
        if tab == "active":
            self.active_tab_btn.config_btn(bg=SIDEBAR, fg=FG_LIGHT)
            self.deleted_tab_btn.config_btn(bg="#c0a080", fg=FG_DARK)
            self.tab_label.config(text="Active Users")
            self.active_btns.pack()
            self.deleted_btns.pack_forget()
            self.form_card.pack(fill="x", pady=(0, 8), before=self.status_label)
        else:
            self.active_tab_btn.config_btn(bg="#c0a080", fg=FG_DARK)
            self.deleted_tab_btn.config_btn(bg=SIDEBAR, fg=FG_LIGHT)
            self.tab_label.config(text="Deleted Users")
            self.active_btns.pack_forget()
            self.deleted_btns.pack()
            self.form_card.pack_forget()
        self._clear_form()
        self.load_users()

    def load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        query = self.search_var.get() if hasattr(self, "search_var") else ""
        con = connect_db()
        cur = con.cursor()
        
        if self.current_tab == "active":
            if query.strip():
                cur.execute(
                    "SELECT id, username, role FROM users WHERE username LIKE ? ORDER BY id",
                    (f"%{query.strip()}%",),
                )
            else:
                cur.execute("SELECT id, username, role FROM users ORDER BY id")
        else:  # deleted tab
            if query.strip():
                cur.execute(
                    "SELECT id, username, role FROM deleted_users WHERE username LIKE ? ORDER BY deleted_date DESC",
                    (f"%{query.strip()}%",),
                )
            else:
                cur.execute("SELECT id, username, role FROM deleted_users ORDER BY deleted_date DESC")
        
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
        if not role or role not in ROLES:
            self._set_status("⚠  Please select a valid role.", "#8b0000")
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
                (username, hash_password(password), role),
            )
            con.commit()
            con.close()
            self.load_users()
            self._clear_form()
            self._set_status(f"✔  User '{username}' created successfully.", "#2d6a2d")
            self.root.lift()
            self.root.focus_force()
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
                (username, hash_password(password), role, self.selected_id),
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
        if self.on_close:
            self.root.after(300, lambda: (self.root.destroy(), self.on_close()))

    def _delete_user(self):
        if not self.selected_id:
            self._set_status("⚠  Select a user to delete.", "#8b0000")
            return

        # Self-delete guard
        if self.current_user_id and self.selected_id == self.current_user_id:
            self._set_status("⚠  You cannot delete your own account.", "#8b0000")
            return

        sel = self.tree.selection()
        username = self.tree.item(sel[0], "values")[1] if sel else "this user"

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Move '{username}' to deleted users?\nYou can restore it later.",
        ):
            return
        
        con = connect_db()
        cur = con.cursor()
        # Get user data
        cur.execute("SELECT id, username, password, role FROM users WHERE id=?", (self.selected_id,))
        user = cur.fetchone()
        if user:
            # Move to deleted_users
            cur.execute(
                "INSERT INTO deleted_users (original_id, username, password, role) VALUES (?, ?, ?, ?)",
                user
            )
            cur.execute("DELETE FROM users WHERE id=?", (self.selected_id,))
        con.commit()
        con.close()
        self.load_users()
        self._clear_form()
        self._set_status(f"✔  User '{username}' moved to deleted users.", "#2d6a2d")
        self.root.lift()
        self.root.focus_force()

    def _restore_user(self):
        if not self.selected_id:
            self._set_status("⚠  Select a user to restore.", "#8b0000")
            return

        sel = self.tree.selection()
        username = self.tree.item(sel[0], "values")[1] if sel else "this user"

        if not messagebox.askyesno("Confirm Restore", f"Restore user '{username}'?"):
            return
        
        con = connect_db()
        cur = con.cursor()
        # Get deleted user data
        cur.execute("SELECT username, password, role FROM deleted_users WHERE id=?", (self.selected_id,))
        user = cur.fetchone()
        if user:
            try:
                # Restore to users table
                cur.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    user
                )
                cur.execute("DELETE FROM deleted_users WHERE id=?", (self.selected_id,))
                con.commit()
                self.load_users()
                self._clear_form()
                self._set_status(f"✔  User '{username}' restored successfully.", "#2d6a2d")
                self.root.lift()
                self.root.focus_force()
            except Exception:
                con.rollback()
                self._set_status("⚠  Username already exists in active users.", "#8b0000")
        con.close()

    def _permanent_delete(self):
        if not self.selected_id:
            self._set_status("⚠  Select a user to permanently delete.", "#8b0000")
            return

        sel = self.tree.selection()
        username = self.tree.item(sel[0], "values")[1] if sel else "this user"

        if not messagebox.askyesno(
            "Confirm Permanent Delete",
            f"Permanently delete '{username}'?\nThis action CANNOT be undone!",
        ):
            return
        
        con = connect_db()
        con.execute("DELETE FROM deleted_users WHERE id=?", (self.selected_id,))
        con.commit()
        con.close()
        self.load_users()
        self._clear_form()
        self._set_status(f"✔  User '{username}' permanently deleted.", "#2d6a2d")
        self.root.lift()
        self.root.focus_force()

    def _clear_form(self):
        self.selected_id = None
        self.entry_username.delete(0, "end")
        self.entry_password.delete(0, "end")
        self.role_var.set("")
        self.combo_role.set("")  # Explicitly clear the combobox
        self.tree.selection_remove(self.tree.selection())
        self._set_status("", auto_clear=False)


if __name__ == "__main__":
    root = tk.Tk()
    # Pass the logged-in user's ID to enable the self-delete guard.
    # Example: UserManagement(root, current_user_id=1)
    UserManagement(root)
    root.mainloop()