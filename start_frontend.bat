@echo off
REM Start Priv Express/React Frontend

echo Starting Priv React Frontend...
echo =================================

REM Set working directory to Priv root
cd /d "C:\Users\kpasc\source\repos\Priv"

echo.
echo Installing dependencies...
echo.
npm install

if %errorlevel% neq 0 (
    echo.
    echo ERROR: npm install failed!
    pause
    exit /b 1
)

echo.
echo Starting development server...
echo =================================
echo.

REM Start the frontend
npm run dev

echo.
echo Frontend stopped.
pause