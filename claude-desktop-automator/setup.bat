@echo off
REM Claude Desktop Automator - Windows Setup Script

echo ============================================
echo Claude Desktop Automator - Setup
echo ============================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check for Poetry
poetry --version >nul 2>&1
if errorlevel 1 (
    echo Poetry not found. Using pip for installation...
    echo.

    REM Create virtual environment
    echo Creating virtual environment...
    python -m venv venv

    REM Activate virtual environment
    call venv\Scripts\activate.bat

    REM Upgrade pip
    echo Upgrading pip...
    python -m pip install --upgrade pip

    REM Install dependencies
    echo Installing dependencies...
    pip install -r requirements.txt

    REM Install in editable mode
    echo Installing claude-automator...
    pip install -e .

    echo.
    echo [SUCCESS] Installation complete!
    echo.
    echo To activate the virtual environment, run:
    echo     venv\Scripts\activate.bat
    echo.
    echo To run the automator:
    echo     python -m claude_automator.cli interactive
    echo.

) else (
    echo [OK] Poetry found
    echo.

    echo Installing dependencies with Poetry...
    poetry install

    echo.
    echo [SUCCESS] Installation complete!
    echo.
    echo To activate the environment, run:
    echo     poetry shell
    echo.
    echo To run the automator:
    echo     poetry run claude-automator interactive
    echo.
)

REM Check for Tesseract
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] Tesseract OCR not found in PATH
    echo.
    echo Tesseract is required for rate limit detection.
    echo Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo.
)

echo ============================================
echo Setup complete!
echo ============================================
echo.
echo Next steps:
echo 1. Make sure Claude Desktop is installed and running
echo 2. Review and customize config/config.yaml
echo 3. Run: python -m claude_automator.cli interactive
echo.

pause
