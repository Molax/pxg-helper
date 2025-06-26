@echo off
echo Installing PokeXGames Helper dependencies...
echo.

REM Check if Python is installed
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH! Please install Python 3.7 or higher.
    echo You can download Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo pip is not installed or not in PATH!
    pause
    exit /b 1
)

echo Installing required packages...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo Error installing packages! Please check error messages above.
    pause
    exit /b 1
)

echo.
echo All dependencies successfully installed!
echo You can now run the helper by executing: python pokexgames_helper.py
echo.
pause