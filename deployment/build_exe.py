"""
Build script for Chizzling POS executable
Run this script to create a standalone executable
"""
import PyInstaller.__main__
import os
import shutil
import time
import sys

# Get the project root directory (parent of deployment folder)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(project_root, 'src')
assets_dir = os.path.join(project_root, 'assets')
food_images_dir = os.path.join(assets_dir, 'food @chizzlin')
logo_ico = os.path.join(assets_dir, 'LOGO.ico')

# Clean previous builds - MORE AGGRESSIVE
dist_dir = os.path.join(project_root, 'dist')
build_dir = os.path.join(project_root, 'build')
deployment_dist = os.path.join(os.path.dirname(__file__), 'dist')
deployment_build = os.path.join(os.path.dirname(__file__), 'build')
spec_file = os.path.join(os.path.dirname(__file__), 'ChizzlingPOS.spec')

exe_path = os.path.join(dist_dir, 'ChizzlingPOS.exe')
deployment_exe = os.path.join(deployment_dist, 'ChizzlingPOS.exe')

# Check if executable is running
for exe in [exe_path, deployment_exe]:
    if os.path.exists(exe):
        try:
            os.remove(exe)
            print(f"Removed old executable: {exe}")
        except PermissionError:
            print("ERROR: ChizzlingPOS.exe is currently running!")
            print("Please close all instances of ChizzlingPOS.exe and try again.")
            print("\nCheck Task Manager (Ctrl+Shift+Esc) if needed.")
            input("\nPress Enter to exit...")
            sys.exit(1)

# Remove all build artifacts
for directory in [dist_dir, build_dir, deployment_dist, deployment_build]:
    if os.path.exists(directory):
        try:
            shutil.rmtree(directory)
            print(f"Cleaned: {directory}")
        except Exception as e:
            print(f"Warning: Could not remove {directory}: {e}")

# Remove spec file to force regeneration
if os.path.exists(spec_file):
    try:
        os.remove(spec_file)
        print(f"Removed spec file: {spec_file}")
    except Exception as e:
        print(f"Warning: Could not remove spec file: {e}")

print("Building Chizzling POS executable...")
print(f"Working directory: {os.path.dirname(__file__)}")

# Change to deployment directory for build
os.chdir(os.path.dirname(__file__))

# PyInstaller arguments
PyInstaller.__main__.run([
    os.path.join(src_dir, 'LoginPage.py'),  # Main entry point
    '--name=ChizzlingPOS',                   # Name of the executable
    '--onefile',                             # Create a single executable file
    '--windowed',                            # No console window (GUI only)
    '--clean',                               # Clean PyInstaller cache
    f'--icon={logo_ico}',                    # Application icon
    f'--add-data={assets_dir};assets',       # Include assets folder
    f'--add-data={food_images_dir};assets/food @chizzlin',  # Include food images
    f'--add-data={src_dir};src',            # Include ALL source files
    '--hidden-import=PIL',                   # Ensure PIL is included
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=tkinter',
    '--hidden-import=sqlite3',
    '--hidden-import=matplotlib.backends.backend_tkagg',
    '--hidden-import=dashboard_views',       # Explicitly include dashboard_views
    '--hidden-import=dashboard_db',          # Explicitly include dashboard_db
    '--hidden-import=dashboard_charts',      # Explicitly include dashboard_charts
    '--exclude-module=PyQt5',
    '--exclude-module=PyQt6',
    '--exclude-module=PySide2',
    '--exclude-module=PySide6',
    '--exclude-module=pytest',
    '--exclude-module=IPython',
    '--exclude-module=jupyter',
    '--exclude-module=notebook',
    '--exclude-module=scipy',
    '--exclude-module=pyarrow',
    '--exclude-module=jedi',
    '--exclude-module=parso',
    '--exclude-module=matplotlib.tests',
    '--exclude-module=numba',
    '--noconfirm',
])

print("\n" + "="*60)
print("BUILD COMPLETE!")
print("="*60)
print(f"\nExecutable location: {os.path.join(dist_dir, 'ChizzlingPOS.exe')}")
print("\nTo distribute:")
print("1. Copy the 'ChizzlingPOS.exe' from the 'dist' folder")
print("2. The database will be created automatically on first run")
print("3. Default login credentials:")
print("   - Admin: username='admin', password='1234'")
print("   - Cashier: username='cashier', password='1234'")
print("   - Inventory Staff: username='inventory_staff', password='1234'")
