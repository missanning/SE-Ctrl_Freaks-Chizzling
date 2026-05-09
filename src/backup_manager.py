import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
from datetime import datetime
import json

# ── Color palette ──────────────────────────────────────────────
BG         = "#ffffff"
ACCENT     = "#f5a623"
YELLOW     = "#ffd966"
BROWN      = "#7a3b10"
FG         = "#3b1f0a"
SUBTLE     = "#7a3b10"
ENTRY_BG   = "#fff8ee"
ENTRY_BORDER = "#f5a623"

FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_LABEL  = ("Segoe UI", 10, "bold")
FONT_ENTRY  = ("Segoe UI", 10)
FONT_BTN    = ("Segoe UI", 10, "bold")
FONT_SMALL  = ("Segoe UI", 9)


def styled_button(parent, text, command, bg=BROWN, fg=YELLOW, width=20):
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=ACCENT, activeforeground=BROWN,
        font=FONT_BTN, relief="flat", bd=0, padx=10, pady=6,
        cursor="hand2", width=width
    )


class BackupManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "sales_inventory.db")
        self.config_path = os.path.join(os.path.dirname(__file__), "backup_config.json")
        self.load_config()

    def load_config(self):
        """Load backup configuration."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {"last_backup": None, "backup_location": None}
        else:
            self.config = {"last_backup": None, "backup_location": None}

    def save_config(self):
        """Save backup configuration."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def create_backup(self, destination=None):
        """Create a backup of the database."""
        if not os.path.exists(self.db_path):
            return False, "Database file not found."

        if not destination:
            destination = self.config.get("backup_location")
            if not destination:
                return False, "No backup location set."

        try:
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"chizzling_backup_{timestamp}.db"
            backup_path = os.path.join(destination, backup_filename)

            # Copy database file
            shutil.copy2(self.db_path, backup_path)

            # Update config
            self.config["last_backup"] = datetime.now().isoformat()
            self.config["backup_location"] = destination
            self.save_config()

            return True, backup_path
        except Exception as e:
            return False, str(e)

    def should_show_reminder(self):
        """Check if backup reminder should be shown (weekly)."""
        last_backup = self.config.get("last_backup")
        if not last_backup:
            return True

        try:
            last_date = datetime.fromisoformat(last_backup)
            days_since = (datetime.now() - last_date).days
            return days_since >= 7
        except:
            return True

    def get_last_backup_info(self):
        """Get information about the last backup."""
        last_backup = self.config.get("last_backup")
        location = self.config.get("backup_location")
       
        if not last_backup:
            return "Never", location or "Not set"
       
        try:
            last_date = datetime.fromisoformat(last_backup)
            days_ago = (datetime.now() - last_date).days
           
            if days_ago == 0:
                time_str = "Today"
            elif days_ago == 1:
                time_str = "Yesterday"
            else:
                time_str = f"{days_ago} days ago"
           
            return time_str, location or "Not set"
        except:
            return "Unknown", location or "Not set"


class BackupWindow:
    def __init__(self, parent):
        self.parent = parent
        self.backup_manager = BackupManager()
        self.create_window()

    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Database Backup")
        self.window.configure(bg=BG)
        self.window.resizable(False, False)
        self.window.grab_set()

        w, h = 500, 500
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"{w}x{h}+{x}+{y}")

        # Banner
        banner = tk.Frame(self.window, bg=BROWN, height=42)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        tk.Label(banner, text="Database Backup Manager", font=FONT_TITLE,
                 bg=BROWN, fg=YELLOW).pack(side="left", padx=16, pady=8)

        tk.Frame(self.window, bg=ACCENT, height=3).pack(fill="x")
        tk.Frame(self.window, bg=YELLOW, height=3).pack(fill="x")

        # Content
        self.content = tk.Frame(self.window, bg=BG, padx=30, pady=20)
        self.content.pack(fill="both", expand=True)
       
        self.build_content()

    def build_content(self):
        """Build or rebuild the content area."""
        # Clear existing content
        for widget in self.content.winfo_children():
            widget.destroy()

        # Info section
        info_frame = tk.Frame(self.content, bg=ENTRY_BG, padx=15, pady=15,
                              highlightbackground=ENTRY_BORDER, highlightthickness=1)
        info_frame.pack(fill="x", pady=(0, 20))

        tk.Label(info_frame, text="📊 Backup Information", font=FONT_LABEL,
                 bg=ENTRY_BG, fg=BROWN, anchor="w").pack(fill="x", pady=(0, 10))

        last_backup, location = self.backup_manager.get_last_backup_info()

        tk.Label(info_frame, text=f"Last Backup: {last_backup}", font=FONT_ENTRY,
                 bg=ENTRY_BG, fg=FG, anchor="w").pack(fill="x", pady=2)
       
        tk.Label(info_frame, text=f"Location: {location}", font=FONT_SMALL,
                 bg=ENTRY_BG, fg=SUBTLE, anchor="w", wraplength=400, justify="left").pack(fill="x", pady=2)

        # Instructions
        tk.Label(self.content, text="💡 Backup Recommendations", font=FONT_LABEL,
                 bg=BG, fg=BROWN, anchor="w").pack(fill="x", pady=(10, 5))
       
        instructions = [
            "• Backup weekly to prevent data loss",
            "• Save to USB drive or external storage",
            "• Keep multiple backup copies",
            "• Test restore occasionally"
        ]
       
        for instruction in instructions:
            tk.Label(self.content, text=instruction, font=FONT_SMALL,
                     bg=BG, fg=FG, anchor="w").pack(fill="x", pady=2)

        # Buttons
        btn_frame = tk.Frame(self.content, bg=BG)
        btn_frame.pack(fill="x", pady=(20, 0))

        styled_button(btn_frame, "💾 Backup Now", self.backup_now,
                      bg=ACCENT, fg=BROWN, width=18).pack(fill="x", pady=4)
       
        styled_button(btn_frame, "📁 Change Location", self.change_location,
                      bg=SUBTLE, fg=YELLOW, width=18).pack(fill="x", pady=4)

    def backup_now(self):
        """Perform backup now."""
        location = self.backup_manager.config.get("backup_location")
       
        if not location:
            messagebox.showinfo("Select Location",
                              "Please select a backup location first.",
                              parent=self.window)
            self.change_location()
            return

        success, result = self.backup_manager.create_backup()
       
        if success:
            messagebox.showinfo("Backup Successful",
                              f"Database backed up successfully!\n\nSaved to:\n{result}",
                              parent=self.window)
            self.window.destroy()
        else:
            messagebox.showerror("Backup Failed",
                               f"Failed to create backup:\n{result}",
                               parent=self.window)

    def change_location(self):
        """Change backup location."""
        folder = filedialog.askdirectory(
            title="Select Backup Location",
            parent=self.window
        )
       
        if folder:
            self.backup_manager.config["backup_location"] = folder
            self.backup_manager.save_config()
            messagebox.showinfo("Location Updated",
                              f"Backup location set to:\n{folder}\n\nYou can now create backups to this location.",
                              parent=self.window)
            # Rebuild content to show updated info
            self.build_content()


def show_backup_reminder(parent):
    """Show backup reminder dialog."""
    backup_manager = BackupManager()
   
    if not backup_manager.should_show_reminder():
        return

    dialog = tk.Toplevel(parent)
    dialog.title("Backup Reminder")
    dialog.configure(bg=BG)
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    w, h = 400, 250
    x = (dialog.winfo_screenwidth() // 2) - (w // 2)
    y = (dialog.winfo_screenheight() // 2) - (h // 2)
    dialog.geometry(f"{w}x{h}+{x}+{y}")

    # Banner
    banner = tk.Frame(dialog, bg=BROWN, height=38)
    banner.pack(fill="x")
    banner.pack_propagate(False)
    tk.Label(banner, text="⚠️ Backup Reminder", font=FONT_TITLE,
             bg=BROWN, fg=YELLOW).pack(side="left", padx=14, pady=6)

    tk.Frame(dialog, bg=ACCENT, height=3).pack(fill="x")
    tk.Frame(dialog, bg=YELLOW, height=3).pack(fill="x")

    # Content
    content = tk.Frame(dialog, bg=BG, padx=30, pady=20)
    content.pack(fill="both", expand=True)

    last_backup, _ = backup_manager.get_last_backup_info()

    tk.Label(content, text="It's time to backup your database!",
             font=FONT_LABEL, bg=BG, fg=BROWN).pack(pady=(0, 10))
   
    tk.Label(content, text=f"Last backup: {last_backup}",
             font=FONT_ENTRY, bg=BG, fg=FG).pack(pady=(0, 20))

    def backup_now():
        dialog.destroy()
        BackupWindow(parent)

    def remind_later():
        dialog.destroy()

    btn_frame = tk.Frame(content, bg=BG)
    btn_frame.pack(fill="x")

    styled_button(btn_frame, "💾 Backup Now", backup_now,
                  bg=ACCENT, fg=BROWN, width=15).pack(side="left", padx=5)
   
    styled_button(btn_frame, "⏰ Remind Later", remind_later,
                  bg=SUBTLE, fg=YELLOW, width=15).pack(side="left", padx=5)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    BackupWindow(root)
    root.mainloop()


