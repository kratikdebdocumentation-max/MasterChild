@echo off
echo ========================================
echo    Master-Child Trading GUI Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found. Checking version...
python --version

REM Check if virtual environment exists
if not exist "trading_env" (
    echo.
    echo Virtual environment not found. Creating one...
    echo This may take a few minutes...
    python -m venv trading_env
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call trading_env\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if requirements are installed
echo.
echo Checking dependencies...
python -c "import tkinter, pandas, requests" >nul 2>&1
if errorlevel 1 (
    echo Dependencies not found. Installing requirements...
    echo This may take a few minutes...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install requirements
        echo Please check your internet connection and try again
        pause
        exit /b 1
    )
    echo Requirements installed successfully.
)

REM Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found in current directory
    echo Please make sure you're running this from the correct folder
    pause
    exit /b 1
)

REM Check if config directory exists
if not exist "config" (
    echo Creating config directory...
    mkdir config
)

REM Check if settings.json exists
if not exist "config\settings.json" (
    echo Creating default settings file...
    echo {} > config\settings.json
)

REM Check if data directory exists
if not exist "data" (
    echo Creating data directory...
    mkdir data
)

REM Check if logs directory exists
if not exist "logs" (
    echo Creating logs directory...
    mkdir logs
)

echo.
echo ========================================
echo    Starting Master-Child Trading GUI
echo ========================================
echo.

REM Run the application
python main.py

REM If the application exits, show message
echo.
echo Application has closed.
echo Press any key to exit...
pause >nul
