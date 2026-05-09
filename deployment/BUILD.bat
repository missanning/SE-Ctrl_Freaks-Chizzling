@echo off
echo ========================================
echo Chizzling POS - Executable Builder
echo ========================================
echo.

echo Step 1: Installing build dependencies...
pip install -r requirements-build.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo Step 2: Building executable...
python build_exe.py
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)
echo.

echo Step 3: Copying database to executable location...
if exist "..\src\sales_inventory.db" (
    copy /Y "..\src\sales_inventory.db" "dist\sales_inventory.db"
    if %errorlevel% equ 0 (
        echo Database copied successfully!
    ) else (
        echo WARNING: Failed to copy database
    )
) else (
    echo WARNING: No database found in src folder.
    echo The application will create a new database on first run.
)
echo.

echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo.
echo Your executable is ready at: dist\ChizzlingPOS.exe
echo Database location: dist\sales_inventory.db
echo.
echo Next steps:
echo 1. Test the executable by running it
echo 2. Login as admin (username: admin, password: 1234)
echo 3. Verify dashboard displays data correctly
echo 4. Copy ChizzlingPOS.exe and sales_inventory.db to distribute
echo 5. See BUILD_GUIDE.md for distribution instructions
echo.
echo IMPORTANT: Always distribute both files together:
echo   - ChizzlingPOS.exe
echo   - sales_inventory.db
echo.
pause
