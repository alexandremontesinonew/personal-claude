#!/bin/bash
# Claude Desktop Automator - Linux/Mac Setup Script

echo "============================================"
echo "Claude Desktop Automator - Setup"
echo "============================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.11+ from https://python.org"
    exit 1
fi

echo "[OK] Python found: $(python3 --version)"
echo ""

# Check for Poetry
if command -v poetry &> /dev/null; then
    echo "[OK] Poetry found"
    echo ""

    echo "Installing dependencies with Poetry..."
    poetry install

    echo ""
    echo "[SUCCESS] Installation complete!"
    echo ""
    echo "To activate the environment, run:"
    echo "    poetry shell"
    echo ""
    echo "To run the automator:"
    echo "    poetry run claude-automator interactive"
    echo ""

else
    echo "Poetry not found. Using pip for installation..."
    echo ""

    # Create virtual environment
    echo "Creating virtual environment..."
    python3 -m venv venv

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip

    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt

    # Install in editable mode
    echo "Installing claude-automator..."
    pip install -e .

    echo ""
    echo "[SUCCESS] Installation complete!"
    echo ""
    echo "To activate the virtual environment, run:"
    echo "    source venv/bin/activate"
    echo ""
    echo "To run the automator:"
    echo "    python -m claude_automator.cli interactive"
    echo ""
fi

# Check for Tesseract
if ! command -v tesseract &> /dev/null; then
    echo ""
    echo "[WARNING] Tesseract OCR not found in PATH"
    echo ""
    echo "Tesseract is required for rate limit detection."
    echo ""
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  macOS: brew install tesseract"
    echo ""
fi

echo "============================================"
echo "Setup complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Make sure Claude Desktop is installed and running"
echo "2. Review and customize config/config.yaml"
echo "3. Run: python -m claude_automator.cli interactive"
echo ""
