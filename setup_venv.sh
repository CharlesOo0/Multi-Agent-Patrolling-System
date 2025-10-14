#!/bin/bash
# filepath: setup_venv.sh

# Simple script to setup Python virtual environment with requirements

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Set Python command
PYTHON_CMD=$(command -v python3 || command -v python)

echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv

echo "Activating virtual environment..."
# Windows (Git Bash) or Linux/Mac
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

echo "Upgrading pip and installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete! Virtual environment ready."
echo "To activate manually: source venv/bin/activate (Linux/Mac) or source venv/Scripts/activate (Windows)"