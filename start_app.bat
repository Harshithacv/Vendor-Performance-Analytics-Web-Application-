@echo off
TITLE Vendor Performance Analytics Launcher
echo ========================================================
echo   VENDOR PERFORMANCE ANALYTICS WEB APPLICATION
echo ========================================================
echo.

REM 1. Start MySQL daemon if not already running
echo [1/3] Checking MySQL Server status...
netstat -ano | findstr 3306 >nul
if %errorlevel% equ 0 (
    echo [OK] MySQL is active on port 3306.
) else (
    echo [INFO] Starting MySQL in user-space daemon...
    start /B "MySQL" "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --defaults-file="C:\Users\91938\.mysql_my.ini" --console
    timeout /t 3 >nul
)

REM 2. Start FastAPI Backend
echo [2/3] Starting FastAPI Backend on http://127.0.0.1:8000 ...
cd backend
start "FastAPI Backend" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM 3. Start React Frontend
echo [3/3] Starting React Vite Frontend on http://127.0.0.1:5173 ...
cd ..\frontend
start "React Frontend" cmd /k "npm run dev -- --host 127.0.0.1 --port 5173"

echo.
echo ========================================================
echo   Application launched successfully!
echo   Frontend: http://127.0.0.1:5173
echo   Backend Docs: http://127.0.0.1:8000/docs
echo   Login: admin@vendoranalytics.com / admin123
echo ========================================================
echo.
pause
