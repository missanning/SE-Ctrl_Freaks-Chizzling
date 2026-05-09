"""
Logout helper for Chizzling POS
Handles logout and restart for both script and executable modes
"""
import tkinter as tk
import sys
import os


def logout_and_restart(current_root):
    """
    Logout and restart the application to login screen.
    Works in both script mode and frozen executable mode.
    """
    try:
        current_root.destroy()
        
        # Create new login window
        new_root = tk.Tk()
        sys.path.insert(0, os.path.dirname(__file__))
        from LoginPage import MainApp
        MainApp(new_root)
        new_root.mainloop()
        
    except Exception as e:
        print(f"Error during logout: {e}")
        # If all else fails, just exit
        sys.exit(0)
